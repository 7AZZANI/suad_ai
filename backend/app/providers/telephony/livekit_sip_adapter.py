"""LiveKit / SIP telephony adapter (local-first default).

LiveKit + a SIP trunk lets you self-host phone access without a cloud
telephony bill. This adapter normalizes LiveKit SIP webhook/JSON events and
renders a simple JSON action the LiveKit agent worker can consume.

Marked a *placeholder* until LIVEKIT_URL/KEY/SECRET are set: parsing works
offline so you can test the call pipeline; live media bridging requires a
running `livekit-agents` worker (see docs/telephony.md).
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.telephony.base import CallEvent, TelephonyProvider, TelephonyResponse

logger = get_logger("app.telephony.livekit")


class LiveKitSIPTelephony(TelephonyProvider):
    name = "livekit_sip"

    def __init__(self) -> None:
        self.configured = bool(
            settings.livekit_url
            and settings.livekit_api_key
            and settings.livekit_api_secret
        )

    def parse_webhook(self, headers: dict[str, str], body: bytes,
                      form: dict[str, str]) -> CallEvent:
        try:
            data: dict[str, Any] = json.loads(body or b"{}")
        except json.JSONDecodeError:
            data = dict(form)
        return CallEvent(
            provider=self.name,
            event=data.get("event", "incoming"),
            call_id=str(data.get("call_id") or data.get("sid") or "unknown"),
            from_number=data.get("from", ""),
            to_number=data.get("to", ""),
            speech_text=data.get("transcript", data.get("speech", "")),
            digits=data.get("dtmf", ""),
            raw=data,
        )

    def render_response(self, response: TelephonyResponse) -> TelephonyResponse:
        response.body = json.dumps({
            "say": response.say,
            "gather": response.gather,
            "hangup": response.hangup,
        })
        response.content_type = "application/json"
        return response

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "configured": self.configured,
            "livekit_url": settings.livekit_url or "(unset)",
            "note": "Local-first SIP. Run a livekit-agents worker for live media."
            if self.configured
            else "Placeholder — set LIVEKIT_URL/API_KEY/API_SECRET in .env.",
        }
