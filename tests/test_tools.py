"""Tool registry + runtime gating (with a fake, deterministic LLM)."""

import pytest

from app.agents import runtime as runtime_mod
from app.agents.runtime import AgentRuntime
from app.core.security import Identity
from app.db.models import Agent
from app.providers.llm.base import LLMResponse, ToolCall
from app.tools import ToolContext
from app.tools.builtin import register_builtin_tools
from app.tools.registry import ToolRegistry, registry


@pytest.fixture(autouse=True)
def _tools():
    register_builtin_tools()


def _agent(allowed="*", role="operator"):
    return Agent(
        id="a1", name="t", description="", system_prompt="sys", role=role,
        allowed_tools=allowed, temperature=0.0, max_tokens=64,
        rag_enabled=False, is_active=True,
    )


def test_registry_register_and_duplicate():
    r = ToolRegistry()
    from app.tools.base import Tool

    async def h(ctx, args):
        from app.tools import ToolResult
        return ToolResult(True, 1)

    t = Tool(name="x", description="d", parameters={"type": "object"}, handler=h)
    r.register(t)
    assert r.get("x") is t
    with pytest.raises(ValueError):
        r.register(t)


def test_builtin_tools_present():
    names = {t.name for t in registry.all()}
    assert {"get_current_time", "order_status_lookup", "create_support_ticket",
            "book_appointment", "human_handoff", "knowledge_search"} <= names


def test_visibility_filtering():
    only = registry.visible_to({"get_current_time"})
    assert [t.name for t in only] == ["get_current_time"]


async def test_order_status_handler_demo_data():
    tool = registry.get("order_status_lookup")
    ctx = ToolContext(identity=Identity("u", "operator"), db=None)
    res = await tool.handler(ctx, {"order_id": "1001"})
    assert res.ok and res.data["status"] == "shipped"


class FakeLLM:
    """Turn 1: ask for a tool. Turn 2: final answer."""

    name = "fake"

    def __init__(self):
        self.turn = 0

    async def chat(self, messages, tools=None, *, temperature=None, max_tokens=None):
        self.turn += 1
        if self.turn == 1:
            return LLMResponse(
                content="",
                tool_calls=[ToolCall(id="c1", name="get_current_time", arguments={})],
            )
        return LLMResponse(content="The time has been fetched.")


async def test_runtime_executes_safe_tool(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(runtime_mod, "get_llm", lambda: fake)
    rt = AgentRuntime(_agent(), Identity("u", "operator"), db=None)
    result = await rt.run_chat("what time is it?")
    assert "fetched" in result.reply
    assert result.tool_invocations[0]["tool"] == "get_current_time"
    assert result.tool_invocations[0]["ok"] is True


class ApprovalLLM(FakeLLM):
    async def chat(self, messages, tools=None, *, temperature=None, max_tokens=None):
        return LLMResponse(
            content="",
            tool_calls=[ToolCall(id="c1", name="book_appointment",
                                 arguments={"service": "x", "when": "y"})],
        )


async def test_runtime_blocks_approval_tool(monkeypatch):
    monkeypatch.setattr(runtime_mod, "get_llm", lambda: ApprovalLLM())
    rt = AgentRuntime(_agent(role="operator"), Identity("u", "operator"), db=None)
    result = await rt.run_chat("book me an appointment")
    assert result.pending_action is not None
    assert result.pending_action.decision == "approval_required"
