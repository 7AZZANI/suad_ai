from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.errors import ProviderNotConfigured
from app.providers.base import ProviderStatus
from app.providers.tts.base import SpeechResult, TTSProvider, synthesize_tone
from app.providers.tts.piper_adapter import build_piper
from app.providers.tts.xtts_adapter import build_xtts


class NullTTS(TTSProvider):
    """Always-available offline synth. Never blocks the Voice Test page."""

    name = "null"

    async def synthesize(self, text: str, *, voice: str | None = None) -> SpeechResult:
        return SpeechResult(audio=synthesize_tone(text or "(empty)"), note="null/tone")

    async def health(self) -> ProviderStatus:
        return ProviderStatus.up(self.name, "Offline tone synth (no real speech).")


def _build() -> TTSProvider:
    provider = settings.tts_provider.lower().strip()
    if provider == "piper":
        return build_piper()
    if provider == "xtts":
        return build_xtts()
    if provider in ("none", "null", ""):
        return NullTTS()
    raise ProviderNotConfigured(
        f"Unsupported TTS_PROVIDER='{provider}'.",
        {"supported": ["piper", "xtts", "null"]},
    )


@lru_cache
def get_tts() -> TTSProvider:
    return _build()
