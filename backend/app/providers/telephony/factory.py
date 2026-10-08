from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.errors import ProviderNotConfigured
from app.providers.telephony.base import TelephonyProvider
from app.providers.telephony.livekit_sip_adapter import LiveKitSIPTelephony
from app.providers.telephony.twilio_adapter import TwilioTelephony


def _build() -> TelephonyProvider:
    provider = settings.telephony_provider.lower().strip()
    if provider == "livekit_sip":
        return LiveKitSIPTelephony()
    if provider == "twilio":
        return TwilioTelephony()
    if provider in ("none", "null", ""):
        raise ProviderNotConfigured("Telephony disabled (TELEPHONY_PROVIDER=null).")
    raise ProviderNotConfigured(
        f"Unsupported TELEPHONY_PROVIDER='{provider}'.",
        {"supported": ["livekit_sip", "twilio", "null"]},
    )


@lru_cache
def get_telephony() -> TelephonyProvider:
    return _build()
