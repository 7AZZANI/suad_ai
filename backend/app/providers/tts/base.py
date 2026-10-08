from __future__ import annotations

import abc
import math
import struct
import wave
from dataclasses import dataclass
from io import BytesIO

from app.providers.base import ProviderStatus


@dataclass
class SpeechResult:
    audio: bytes
    content_type: str = "audio/wav"
    sample_rate: int = 22050
    note: str = ""


def synthesize_tone(text: str, sample_rate: int = 22050) -> bytes:
    """Deterministic offline fallback: encode text length as a short WAV tone.

    Guarantees the Voice Test page produces audible output even with zero
    speech dependencies installed — true local-first behaviour.
    """
    duration = min(2.5, 0.4 + len(text) * 0.03)
    freq = 320.0
    n = int(sample_rate * duration)
    buf = BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n):
            env = min(1.0, i / 800) * min(1.0, (n - i) / 800)
            sample = int(0.3 * env * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            frames += struct.pack("<h", sample)
        w.writeframes(bytes(frames))
    return buf.getvalue()


class TTSProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def synthesize(self, text: str, *, voice: str | None = None) -> SpeechResult: ...

    @abc.abstractmethod
    async def health(self) -> ProviderStatus: ...
