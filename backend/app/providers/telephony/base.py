"""Telephony provider interface.

Goal: a new phone vendor = one new adapter. The webhook route only ever sees
a normalized :class:`CallEvent` and returns a provider-rendered
:class:`TelephonyResponse`, so call-handling logic is vendor-independent.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CallEvent:
    """Normalized inbound telephony event."""

    provider: str
    event: str  # incoming | speech | dtmf | hangup
    call_id: str
    from_number: str = ""
    to_number: str = ""
    speech_text: str = ""
    digits: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class TelephonyResponse:
    """Instruction for the provider: speak text, then gather or hang up."""

    say: str = ""
    gather: bool = True
    hangup: bool = False
    body: str = ""          # provider-native rendered payload (e.g. TwiML)
    content_type: str = "application/json"


class TelephonyProvider(abc.ABC):
    name: str = "base"
    configured: bool = False

    @abc.abstractmethod
    def parse_webhook(self, headers: dict[str, str], body: bytes,
                      form: dict[str, str]) -> CallEvent: ...

    @abc.abstractmethod
    def render_response(self, response: TelephonyResponse) -> TelephonyResponse: ...

    @abc.abstractmethod
    def status(self) -> dict[str, Any]: ...
