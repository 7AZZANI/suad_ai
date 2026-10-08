"""Anthropic Claude LLM adapter.

Maps the common :class:`ChatMessage`/:class:`ToolSpec` interface onto the
Anthropic Messages API (system prompt is separated, tool calls use
``tool_use``/``tool_result`` blocks). SDK imported lazily.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import ProviderStatus
from app.providers.llm.base import ChatMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec

logger = get_logger("app.llm.anthropic")


class AnthropicLLM(LLMProvider):
    name = "anthropic"

    def __init__(self, *, api_key: str, model: str, timeout: int = 60) -> None:
        self._api_key = api_key
        self._model = model or "claude-sonnet-4"
        self._timeout = timeout
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if not self._api_key:
            raise ProviderError(
                "ANTHROPIC_API_KEY is not set. Add it to .env to use Claude.",
            )
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError as exc:  # pragma: no cover
                raise ProviderError(
                    "The `anthropic` package is required. `pip install anthropic`.",
                ) from exc
            self._client = AsyncAnthropic(api_key=self._api_key, timeout=self._timeout)
        return self._client

    @staticmethod
    def _split(messages: list[ChatMessage]) -> tuple[str, list[dict[str, Any]]]:
        system_parts: list[str] = []
        out: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            elif m.role == "tool":
                out.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.tool_call_id or "tool_0",
                        "content": m.content,
                    }],
                })
            else:
                out.append({"role": m.role, "content": m.content})
        return "\n\n".join(system_parts), out

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        client = self._get_client()
        system, conv = self._split(messages)
        kwargs: dict[str, Any] = {
            "model": self._model,
            "system": system or "You are a helpful assistant.",
            "messages": conv,
            "max_tokens": settings.llm_max_tokens if max_tokens is None else max_tokens,
            "temperature": settings.llm_temperature if temperature is None else temperature,
        }
        if tools:
            kwargs["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.parameters}
                for t in tools
            ]

        try:
            resp = await client.messages.create(**kwargs)
        except Exception as exc:  # pragma: no cover - network dependent
            raise ProviderError(
                "Claude request failed.", {"model": self._model, "cause": str(exc)}
            ) from exc

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=dict(block.input))
                )
        return LLMResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            finish_reason=resp.stop_reason or "stop",
        )

    async def health(self) -> ProviderStatus:
        try:
            client = self._get_client()
            await client.messages.create(
                model=self._model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return ProviderStatus.up(self.name, f"model={self._model}")
        except Exception as exc:  # pragma: no cover
            return ProviderStatus.down(self.name, f"Unreachable: {exc}", model=self._model)
