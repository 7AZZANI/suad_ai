"""LLM factory — selects the adapter purely from settings.

Adding a new vendor that speaks the OpenAI API is a one-line `.env` change.
Adding a genuinely new protocol means: write an adapter implementing
``LLMProvider`` and register it in ``_BUILDERS`` below.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.errors import ConfigurationError
from app.providers.llm.anthropic_adapter import AnthropicLLM
from app.providers.llm.base import LLMProvider
from app.providers.llm.openai_compatible import OpenAICompatibleLLM

# Providers that all speak the OpenAI-compatible protocol.
_OPENAI_COMPATIBLE = {"ollama", "vllm", "lmstudio", "openrouter", "openai", "dashscope"}


def _build() -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    if provider in _OPENAI_COMPATIBLE:
        return OpenAICompatibleLLM(
            provider=provider,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
        )
    if provider == "anthropic":
        return AnthropicLLM(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
        )
    raise ConfigurationError(
        f"Unknown LLM_PROVIDER='{provider}'.",
        {"supported": sorted(_OPENAI_COMPATIBLE | {"anthropic"})},
    )


@lru_cache
def get_llm() -> LLMProvider:
    return _build()
