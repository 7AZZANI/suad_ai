"""Agent runtime — provider-agnostic chat + tool orchestration.

Pipeline:
  1. assemble messages: system + RAG context + recipe guidance + history + user
  2. ask the LLM (with the tools this agent is allowed to use)
  3. for each requested tool call: run it through the permission engine
       - allowed       -> execute the typed handler, feed result back
       - confirm/approval -> stop and surface a pending action to the caller
  4. repeat until the LLM produces a final answer (bounded iterations)

The runtime never trusts the LLM to act — every tool passes the gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import Identity
from app.db.models import Agent
from app.permissions import permission_engine
from app.providers.llm import ChatMessage, get_llm
from app.providers.memory import get_memory
from app.tasks import load_recipe
from app.tools import ToolContext
from app.tools.registry import registry

logger = get_logger("app.agents")

MAX_TOOL_ITERATIONS = 4


@dataclass
class PendingAction:
    tool_name: str
    decision: str  # confirm_required | approval_required
    reason: str
    arguments: dict[str, Any]
    approval_id: str | None = None


@dataclass
class ChatTurnResult:
    reply: str
    tool_invocations: list[dict[str, Any]] = field(default_factory=list)
    pending_action: PendingAction | None = None
    used_rag: bool = False
    citations: list[dict[str, Any]] = field(default_factory=list)


class AgentRuntime:
    def __init__(self, agent: Agent, identity: Identity, db: AsyncSession | None) -> None:
        self.agent = agent
        self.identity = identity
        self.db = db
        self.llm = get_llm()
        self.memory = get_memory()

    async def _retrieval_context(self, query: str) -> tuple[str, list[dict[str, Any]]]:
        if not (self.agent.rag_enabled and self.memory.enabled):
            return "", []
        try:
            chunks = await self.memory.search(query, k=4)
        except Exception as exc:  # RAG is optional — never break the chat
            logger.warning("rag search failed: %s", exc)
            return "", []
        if not chunks:
            return "", []
        ctx = "\n\n".join(f"- {c.text}" for c in chunks)
        cites = [{"text": c.text[:200], "score": c.score, **c.metadata} for c in chunks]
        return ctx, cites

    def _system_prompt(self, recipe_name: str | None) -> str:
        parts = [self.agent.system_prompt]
        if recipe_name:
            recipe = load_recipe(recipe_name)
            parts.append(f"\n## Task: {recipe.title}\n{recipe.guidance}")
            if recipe.steps:
                parts.append("Steps:\n" + "\n".join(f"{i+1}. {s}"
                             for i, s in enumerate(recipe.steps)))
        return "\n".join(parts)

    async def run_chat(
        self,
        user_message: str,
        history: list[ChatMessage] | None = None,
        *,
        recipe_name: str | None = None,
        confirm: bool = False,
        approval_id: str | None = None,
    ) -> ChatTurnResult:
        allowed = self.agent.allowed_tool_set()
        specs = registry.specs_for(allowed)

        rag_ctx, citations = await self._retrieval_context(user_message)
        system = self._system_prompt(recipe_name)
        if rag_ctx:
            system += (
                "\n\n## Knowledge base context (use if relevant, do not fabricate)\n"
                + rag_ctx
            )

        messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
        messages += history or []
        messages.append(ChatMessage(role="user", content=user_message))

        invocations: list[dict[str, Any]] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            resp = await self.llm.chat(
                messages,
                tools=specs or None,
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
            )
            if not resp.wants_tools:
                return ChatTurnResult(
                    reply=resp.content or "(no response)",
                    tool_invocations=invocations,
                    used_rag=bool(rag_ctx),
                    citations=citations,
                )

            messages.append(ChatMessage(role="assistant", content=resp.content or ""))
            for call in resp.tool_calls:
                pending = await self._handle_tool_call(call, messages, invocations,
                                                       confirm, approval_id)
                if pending is not None:
                    return ChatTurnResult(
                        reply=(
                            f"I need authorization to run '{pending.tool_name}'. "
                            f"{pending.reason}"
                        ),
                        tool_invocations=invocations,
                        pending_action=pending,
                        used_rag=bool(rag_ctx),
                        citations=citations,
                    )

        return ChatTurnResult(
            reply="I wasn't able to complete this within the step limit.",
            tool_invocations=invocations,
            used_rag=bool(rag_ctx),
            citations=citations,
        )

    async def _handle_tool_call(
        self,
        call: Any,
        messages: list[ChatMessage],
        invocations: list[dict[str, Any]],
        confirm: bool,
        approval_id: str | None,
    ) -> PendingAction | None:
        try:
            tool = registry.get(call.name)
        except Exception:
            messages.append(ChatMessage(role="tool", content=f"Unknown tool {call.name}",
                                        name=call.name, tool_call_id=call.id))
            return None

        decision = await permission_engine.evaluate(
            db=self.db,
            identity=self.identity,
            tool_name=tool.name,
            required_scope=tool.scope,
            risk_level=tool.risk_level,
            arguments=call.arguments,
            confirm=confirm,
            approval_id=approval_id,
            agent_id=self.agent.id,
        )

        if not decision.allowed:
            if decision.decision in ("confirm_required", "approval_required"):
                return PendingAction(
                    tool_name=tool.name,
                    decision=decision.decision,
                    reason=decision.reason,
                    arguments=call.arguments,
                    approval_id=decision.approval_id,
                )
            messages.append(ChatMessage(
                role="tool",
                content=f"Permission denied: {decision.reason}",
                name=tool.name, tool_call_id=call.id,
            ))
            invocations.append({"tool": tool.name, "decision": decision.decision,
                                "ok": False})
            return None

        ctx = ToolContext(identity=self.identity, db=self.db, agent_id=self.agent.id)
        try:
            result = await tool.handler(ctx, call.arguments)
        except Exception as exc:
            logger.exception("tool %s failed", tool.name)
            result_payload, ok, summary = None, False, f"Tool error: {exc}"
        else:
            result_payload, ok, summary = result.data, result.ok, result.summary()

        messages.append(ChatMessage(
            role="tool",
            content=str({"ok": ok, "data": result_payload, "message": summary}),
            name=tool.name, tool_call_id=call.id,
        ))
        invocations.append({"tool": tool.name, "decision": "allowed",
                            "ok": ok, "summary": summary})
        return None
