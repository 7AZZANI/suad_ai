"""Twilio telephony adapter (optional cloud option).

Parses Twilio's form-encoded voice webhook and renders TwiML. Placeholder
until TWILIO_* credentials are set; webhook parsing/TwiML rendering work
offline so the flow is testable without an account.
"""

from __future__ import annotations

from typing import Any
from xml.sax.saxutils import escape

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.telephony.base import CallEvent, TelephonyProvider, TelephonyResponse

logger = get_logger("app.telephony.twilio")


class TwilioTelephony(TelephonyProvider):
    name = "twilio"

    def __init__(self) -> None:
        self.configured = bool(
            settings.twilio_account_sid
            and settings.twilio_auth_token
            and settings.twilio_phone_number
        )

    def parse_webhook(self, headers: dict[str, str], body: bytes,
                      form: dict[str, str]) -> CallEvent:
        digits = form.get("Digits", "")
        speech = form.get("SpeechResult", "")
        event = "speech" if speech else "dtmf" if digits else "incoming"
        if form.get("CallStatus") in {"completed", "canceled", "failed"}:
            event = "hangup"
        return CallEvent(
            provider=self.name,
            event=event,
            call_id=form.get("CallSid", "unknown"),
            from_number=form.get("From", ""),
            to_number=form.get("To", ""),
            speech_text=speech,
            digits=digits,
            raw=dict(form),
        )

    def render_response(self, response: TelephonyResponse) -> TelephonyResponse:
        say = escape(response.say or "")
        parts = ['<?xml version="1.0" encoding="UTF-8"?>', "<Response>"]
        if response.hangup:
            if say:
                parts.append(f"<Say>{say}</Say>")
            parts.append("<Hangup/>")
        elif response.gather:
            parts.append(
                '<Gather input="speech dtmf" timeout="5" '
                'speechTimeout="auto" action="/api/telephony/twilio/webhook">'
                f"<Say>{say}</Say></Gather>"
            )
            parts.append("<Redirect>/api/telephony/twilio/webhook</Redirect>")
        else:
            parts.append(f"<Say>{say}</Say>")
        parts.append("</Response>")
        response.body = "".join(parts)
        response.content_type = "application/xml"
        return response

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "configured": self.configured,
            "from_number": settings.twilio_phone_number or "(unset)",
            "note": "Ready." if self.configured
            else "Placeholder — set TWILIO_ACCOUNT_SID/AUTH_TOKEN/PHONE_NUMBER.",
        }
