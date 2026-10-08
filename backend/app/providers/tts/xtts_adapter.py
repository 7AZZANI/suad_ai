"""Local TTS via Coqui XTTS (multilingual, voice-cloning capable).

Heavier than Piper; the model is loaded lazily and falls back to the offline
tone generator if Coqui TTS is not installed.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import ProviderStatus
from app.providers.tts.base import SpeechResult, TTSProvider, synthesize_tone

logger = get_logger("app.tts.xtts")


class XTTS(TTSProvider):
    name = "xtts"

    def __init__(self, *, model: str) -> None:
        self._model_name = model
        self._tts: Any | None = None

    def _load(self) -> Any | None:
        if self._tts is None:
            try:
                from TTS.api import TTS as CoquiTTS
            except ImportError:
                return None
            logger.info("loading xtts model=%s", self._model_name)
            self._tts = CoquiTTS(self._model_name)
        return self._tts

    def _synth_sync(self, text: str) -> SpeechResult:
        tts = self._load()
        if tts is None:
            return SpeechResult(
                audio=synthesize_tone(text),
                note="Coqui TTS not installed — tone fallback. `pip install TTS`.",
            )
        with tempfile.NamedTemporaryFile(suffix=".wav") as out:
            tts.tts_to_file(text=text, file_path=out.name, language="en")
            return SpeechResult(audio=Path(out.name).read_bytes(), note="xtts")

    async def synthesize(self, text: str, *, voice: str | None = None) -> SpeechResult:
        return await asyncio.to_thread(self._synth_sync, text.strip() or "(empty)")

    async def health(self) -> ProviderStatus:
        try:
            import TTS  # noqa: F401
        except ImportError:
            return ProviderStatus.up(
                self.name, "Coqui TTS not installed — tone fallback.", fallback=True
            )
        return ProviderStatus.up(self.name, f"model={self._model_name} (lazy load)")


def build_xtts() -> XTTS:
    return XTTS(model=settings.xtts_model)
