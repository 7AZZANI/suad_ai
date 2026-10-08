"""Local TTS via the Piper binary.

Piper is a fast, fully offline neural TTS. If the binary or a voice model is
not available we degrade gracefully to :func:`synthesize_tone` so the Voice
Test page still works — and we say so in ``note``.
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import ProviderStatus
from app.providers.tts.base import SpeechResult, TTSProvider, synthesize_tone

logger = get_logger("app.tts.piper")


class PiperTTS(TTSProvider):
    name = "piper"

    def __init__(self, *, binary: str, voice: str) -> None:
        self._binary = binary
        self._voice = voice

    def _binary_path(self) -> str | None:
        return shutil.which(self._binary)

    async def synthesize(self, text: str, *, voice: str | None = None) -> SpeechResult:
        text = text.strip()
        if not text:
            text = "(empty)"
        model = voice or self._voice
        binary = self._binary_path()
        if not binary or not model or not Path(model).exists():
            return SpeechResult(
                audio=synthesize_tone(text),
                note="Piper binary/voice not configured — using offline tone "
                "fallback. Set TTS_VOICE to a Piper .onnx model for real speech.",
            )
        with tempfile.NamedTemporaryFile(suffix=".wav") as out:
            proc = await asyncio.create_subprocess_exec(
                binary, "--model", model, "--output_file", out.name,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, err = await proc.communicate(text.encode())
            if proc.returncode != 0:
                logger.warning("piper failed rc=%s err=%s", proc.returncode, err[:200])
                return SpeechResult(audio=synthesize_tone(text), note="Piper failed; tone fallback.")
            return SpeechResult(audio=Path(out.name).read_bytes(), note="piper")

    async def health(self) -> ProviderStatus:
        binary = self._binary_path()
        if not binary:
            return ProviderStatus.up(
                self.name, "Piper binary missing — tone fallback active.", fallback=True
            )
        if not self._voice:
            return ProviderStatus.up(
                self.name, "Piper installed; no TTS_VOICE set — tone fallback.", fallback=True
            )
        return ProviderStatus.up(self.name, f"binary={binary} voice={self._voice}")


def build_piper() -> PiperTTS:
    return PiperTTS(binary=settings.tts_piper_binary, voice=settings.tts_voice)
