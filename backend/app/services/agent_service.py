"""Agent lifecycle + chat/voice orchestration with resilient persistence.

If the database is down, chat still works (history just isn't saved) so the
platform stays demonstrable in a pure local setup.
"""

from __future__ import annotations

import base64
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentRuntime
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.core.security import Identity
from app.db.models import Agent, Conversation, Message
from app.providers.llm import ChatMessage
from app.providers.stt import get_stt
from app.providers.tts import get_tts

logger = get_logger("app.services.agent")

DEFAULT_AGENT = {
    "name": "default",
    "description": "General-purpose business assistant.",
    "system_prompt": (
        "You are Suad, a professional AI employee for a business. Be concise, "
        "accurate and polite. Use tools when they help. Never invent order "
        "numbers, prices or policies — look them up or say you don't know."
    ),
    "role": "operator",
    "allowed_tools": "*",
}


async def ensure_default_agent(db: AsyncSession) -> Agent:
    agent = (
        await db.execute(select(Agent).where(Agent.name == "default"))
    ).scalar_one_or_none()
    if agent is None:
        agent = Agent(**DEFAULT_AGENT)
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
    return agent


async def list_agents(db: AsyncSession) -> list[Agent]:
    return list((await db.execute(select(Agent))).scalars().all())


async def get_agent(db: AsyncSession, agent_id: str) -> Agent:
    agent = (
        await db.execute(
            select(Agent).where((Agent.id == agent_id) | (Agent.name == agent_id))
        )
    ).scalar_one_or_none()
    if agent is None:
        raise NotFoundError(f"Agent '{agent_id}' not found.")
    return agent


async def create_agent(db: AsyncSession, data: dict[str, Any]) -> Agent:
    agent = Agent(**data)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def _load_history(db: AsyncSession | None, conversation_id: str | None,
                        limit: int = 12) -> tuple[str | None, list[ChatMessage]]:
    if not (db and conversation_id):
        return conversation_id, []
    rows = (
        await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    history = [
        ChatMessage(role=m.role, content=m.content)
        for m in reversed(rows)
        if m.role in ("user", "assistant")
    ]
    return conversation_id, history


async def _persist(db: AsyncSession | None, agent: Agent, conversation_id: str | None,
                   channel: str, subject: str, user_msg: str,
                   reply: str) -> str | None:
    if db is None:
        return conversation_id
    try:
        if conversation_id is None:
            conv = Conversation(agent_id=agent.id, channel=channel, subject=subject)
            db.add(conv)
            await db.flush()
            conversation_id = conv.id
        db.add(Message(conversation_id=conversation_id, role="user", content=user_msg))
        db.add(Message(conversation_id=conversation_id, role="assistant", content=reply))
        await db.commit()
    except Exception:  # persistence is best-effort
        logger.warning("conversation persist failed")
    return conversation_id


async def chat(
    db: AsyncSession | None,
    *,
    agent: Agent,
    identity: Identity,
    message: str,
    conversation_id: str | None = None,
    recipe_name: str | None = None,
    confirm: bool = False,
    approval_id: str | None = None,
    channel: str = "chat",
) -> dict[str, Any]:
    conversation_id, history = await _load_history(db, conversation_id)
    runtime = AgentRuntime(agent, identity, db)
    result = await runtime.run_chat(
        message, history, recipe_name=recipe_name,
        confirm=confirm, approval_id=approval_id,
    )
    conversation_id = await _persist(
        db, agent, conversation_id, channel, identity.subject, message, result.reply
    )
    return {
        "agent_id": agent.id,
        "conversation_id": conversation_id,
        "reply": result.reply,
        "tool_invocations": result.tool_invocations,
        "pending_action": (
            result.pending_action.__dict__ if result.pending_action else None
        ),
        "used_rag": result.used_rag,
        "citations": result.citations,
    }


async def voice_turn(
    db: AsyncSession | None,
    *,
    agent: Agent,
    identity: Identity,
    audio: bytes,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Full voice loop: STT -> agent chat -> TTS."""
    transcript = await get_stt().transcribe(audio)
    chat_result = await chat(
        db, agent=agent, identity=identity, message=transcript.text,
        conversation_id=conversation_id, channel="voice",
    )
    speech = await get_tts().synthesize(chat_result["reply"])
    return {
        "transcript": transcript.text,
        "language": transcript.language,
        "reply": chat_result["reply"],
        "conversation_id": chat_result["conversation_id"],
        "audio_note": speech.note,
        "audio_base64": base64.b64encode(speech.audio).decode(),
        "content_type": speech.content_type,
    }
