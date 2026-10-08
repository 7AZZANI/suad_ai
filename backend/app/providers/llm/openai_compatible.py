"""OpenAI-compatible LLM adapter.

Covers Ollama, vLLM, LM Studio, OpenRouter, OpenAI and Alibaba DashScope —
they all expose the same `/v1/chat/completions` contract. The only thing that
changes between them is base URL / API key / model, all from `.env`.

The `openai` SDK is imported lazily so the platform boots even when it (or a
provider) is not installed/reachable.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import ProviderStatus
from app.providers.llm.base import ChatMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec

logger = get_logger("app.llm.openai_compatible")


class OpenAICompatibleLLM(LLMProvider):
    def __init__(
        self,
        *,
        provider: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 60,
    ) -> None:
        self.name = provider
        self._base_url = base_url
        self._api_key = api_key or "not-needed"
        self._model = model
        self._timeout = timeout
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as exc:  # pragma: no cover
                raise ProviderError(
                    "The `openai` package is required for OpenAI-compatible LLM "
                    "providers. Install with `pip install openai`.",
                ) from exc
            self._client = AsyncOpenAI(
                base_url=self._base_url,
                api_key=self._api_key,
                timeout=self._timeout,
            )
        return self._client

    @staticmethod
    def _to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            msg: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.role == "tool":
                msg["tool_call_id"] = m.tool_call_id or "call_0"
                msg["name"] = m.name or "tool"
            out.append(msg)
        return out

    @staticmethod
    def _to_openai_tools(tools: list[ToolSpec] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._to_openai_messages(messages),
            "temperature": settings.llm_temperature if temperature is None else temperature,
            "max_tokens": settings.llm_max_tokens if max_tokens is None else max_tokens,
        }
        oai_tools = self._to_openai_tools(tools)
        if oai_tools:
            kwargs["tools"] = oai_tools
            kwargs["tool_choice"] = "auto"

        try:
            resp = await client.chat.completions.create(**kwargs)
        except Exception as exc:  # pragma: no cover - network dependent
            raise ProviderError(
                f"LLM request failed ({self.name}).",
                {"model": self._model, "cause": str(exc)},
            ) from exc

        choice = resp.choices[0]
        msg = choice.message
        tool_calls: list[ToolCall] = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        return LLMResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
        )

    async def health(self) -> ProviderStatus:
        try:
            client = self._get_client()
            await client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return ProviderStatus.up(self.name, f"model={self._model}")
        except Exception as exc:  # pragma: no cover - network dependent
            return ProviderStatus.down(
                self.name,
                f"Unreachable: {exc}",
                base_url=self._base_url,
                model=self._model,
            )
