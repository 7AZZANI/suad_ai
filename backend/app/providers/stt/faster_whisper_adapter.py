"""Local STT via faster-whisper (CTranslate2). No cloud, no API key.

The model is loaded lazily on first use and cached, so importing this module
(and booting the API) never requires the heavy dependency to be installed.
"""

from __future__ import annotations

import asyncio
import tempfile
from typing import Any

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import ProviderStatus
from app.providers.stt.base import STTProvider, TranscriptResult

logger = get_logger("app.stt.faster_whisper")


class FasterWhisperSTT(STTProvider):
    name = "faster_whisper"

    def __init__(self, *, model: str, device: str, compute_type: str) -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._model: Any | None = None

    def _load(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:  # pragma: no cover
                raise ProviderError(
                    "faster-whisper is not installed. `pip install faster-whisper` "
                    "or switch STT_PROVIDER.",
                ) from exc
            device = None if self._device == "auto" else self._device
            logger.info("loading whisper model=%s", self._model_name)
            self._model = WhisperModel(
                self._model_name,
                device=device or "cpu",
                compute_type=self._compute_type,
            )
        return self._model

    def _transcribe_sync(self, audio: bytes, language: str | None) -> TranscriptResult:
        model = self._load()
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            tmp.write(audio)
            tmp.flush()
            segments, info = model.transcribe(
                tmp.name,
                language=language or (settings.stt_language or None),
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
        return TranscriptResult(
            text=text,
            language=getattr(info, "language", "") or "",
            duration_seconds=getattr(info, "duration", 0.0) or 0.0,
        )

    async def transcribe(
        self, audio: bytes, *, language: str | None = None
    ) -> TranscriptResult:
        if not audio:
            raise ProviderError("Empty audio payload.")
        return await asyncio.to_thread(self._transcribe_sync, audio, language)

    async def health(self) -> ProviderStatus:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return ProviderStatus.down(
                self.name, "faster-whisper not installed (provider import-only)."
            )
        return ProviderStatus.up(
            self.name, f"model={self._model_name} (loads on first use)"
        )
