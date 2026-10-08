from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.errors import ProviderNotConfigured
from app.providers.base import ProviderStatus
from app.providers.stt.base import STTProvider, TranscriptResult
from app.providers.stt.faster_whisper_adapter import FasterWhisperSTT


class NullSTT(STTProvider):
    name = "null"

    async def transcribe(self, audio: bytes, *, language: str | None = None) -> TranscriptResult:
        raise ProviderNotConfigured(
            "STT is disabled (STT_PROVIDER=null). Set a provider to use voice."
        )

    async def health(self) -> ProviderStatus:
        return ProviderStatus.up(self.name, "STT disabled by configuration.")


def _build() -> STTProvider:
    provider = settings.stt_provider.lower().strip()
    if provider in ("faster_whisper", "faster-whisper"):
        return FasterWhisperSTT(
            model=settings.stt_model,
            device=settings.stt_device,
            compute_type=settings.stt_compute_type,
        )
    if provider in ("none", "null", ""):
        return NullSTT()
    # 'openai' (Whisper API) intentionally not bundled by default; add an
    # adapter here mirroring FasterWhisperSTT to enable cloud STT.
    raise ProviderNotConfigured(
        f"Unsupported STT_PROVIDER='{provider}'.",
        {"supported": ["faster_whisper", "null"]},
    )


@lru_cache
def get_stt() -> STTProvider:
    return _build()
