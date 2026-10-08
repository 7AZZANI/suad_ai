"""LLM provider interface.

A provider takes a list of :class:`ChatMessage` (+ optional tool specs) and
returns an :class:`LLMResponse` that is either free text or a request to call
one or more tools. The agent runtime is provider-agnostic — it only speaks
this interface.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from app.providers.base import ProviderStatus


@dataclass
class ChatMessage:
    role: str  # system | user | assistant | tool
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class ToolSpec:
    """JSON-schema description of a callable tool, passed to the model."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    raw: dict[str, Any] | None = None

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


class LLMProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse: ...

    @abc.abstractmethod
    async def health(self) -> ProviderStatus: ...
