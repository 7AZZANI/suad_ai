"""Provider factories must select adapters purely from settings."""

import pytest

from app.core.errors import ConfigurationError
from app.providers.llm.anthropic_adapter import AnthropicLLM
from app.providers.llm.factory import _build as build_llm
from app.providers.memory.factory import NullMemory
from app.providers.memory.factory import _build as build_memory
from app.providers.memory.qdrant_adapter import QdrantMemory
from app.providers.stt.factory import NullSTT
from app.providers.stt.factory import _build as build_stt
from app.providers.stt.faster_whisper_adapter import FasterWhisperSTT
from app.providers.telephony.factory import _build as build_tel
from app.providers.telephony.twilio_adapter import TwilioTelephony
from app.providers.tts.factory import NullTTS
from app.providers.tts.factory import _build as build_tts


@pytest.mark.parametrize(
    "provider", ["ollama", "vllm", "lmstudio", "openrouter", "openai", "dashscope"]
)
def test_openai_compatible_providers(patch_settings, provider):
    patch_settings(llm_provider=provider)
    llm = build_llm()
    assert llm.name == provider


def test_anthropic_provider_selected(patch_settings):
    patch_settings(llm_provider="anthropic")
    assert isinstance(build_llm(), AnthropicLLM)


def test_unknown_llm_raises(patch_settings):
    patch_settings(llm_provider="does-not-exist")
    with pytest.raises(ConfigurationError):
        build_llm()


def test_stt_factory(patch_settings):
    patch_settings(stt_provider="faster_whisper")
    assert isinstance(build_stt(), FasterWhisperSTT)
    patch_settings(stt_provider="null")
    assert isinstance(build_stt(), NullSTT)


def test_tts_factory(patch_settings):
    patch_settings(tts_provider="null")
    assert isinstance(build_tts(), NullTTS)


def test_memory_factory_respects_rag_toggle(patch_settings):
    patch_settings(rag_enabled=False, memory_provider="qdrant")
    assert isinstance(build_memory(), NullMemory)
    patch_settings(rag_enabled=True, memory_provider="qdrant")
    assert isinstance(build_memory(), QdrantMemory)


def test_telephony_factory(patch_settings):
    patch_settings(telephony_provider="twilio")
    assert isinstance(build_tel(), TwilioTelephony)
