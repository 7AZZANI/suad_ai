"""Tool primitives.

A tool is a typed, schema-described capability the LLM may *request*. The LLM
never executes anything itself — the runtime validates the request, runs it
through the permission engine, then calls the Python handler. The handler is
the only thing that touches the database, and it uses safe typed accessors
(never LLM-authored SQL).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Identity
from app.permissions.models import RiskLevel


@dataclass
class ToolContext:
    """Everything a handler is allowed to use. No global state."""

    identity: Identity
    db: AsyncSession | None
    agent_id: str | None = None


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    message: str = ""

    def summary(self) -> str:
        return self.message or ("ok" if self.ok else "failed")


Handler = Callable[[ToolContext, dict[str, Any]], Awaitable[ToolResult]]


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema
    handler: Handler
    scope: str = "tools:read"
    risk_level: RiskLevel = RiskLevel.SAFE
    tags: list[str] = field(default_factory=list)

    def openai_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
