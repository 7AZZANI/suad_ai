from __future__ import annotations

import abc
from dataclasses import dataclass

from app.providers.base import ProviderStatus


@dataclass
class TranscriptResult:
    text: str
    language: str = ""
    duration_seconds: float = 0.0


class STTProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def transcribe(self, audio: bytes, *, language: str | None = None) -> TranscriptResult:
        ...

    @abc.abstractmethod
    async def health(self) -> ProviderStatus: ...
