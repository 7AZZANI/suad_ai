from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.logging import get_logger
from app.core.security import Identity
from app.db.models import CallLog
from app.providers.telephony import TelephonyProvider, TelephonyResponse, get_telephony
from app.providers.telephony.livekit_sip_adapter import LiveKitSIPTelephony
from app.providers.telephony.twilio_adapter import TwilioTelephony
from app.services import agent_service

_ADAPTERS: dict[str, type[TelephonyProvider]] = {
    "livekit_sip": LiveKitSIPTelephony,
    "twilio": TwilioTelephony,
}

router = APIRouter(prefix="/api/telephony", tags=["telephony"])
logger = get_logger("app.api.telephony")


@router.get("/status")
async def status() -> dict:
    try:
        return get_telephony().status()
    except Exception as exc:
        return {"provider": "none", "configured": False, "detail": str(exc)}


@router.get("/calls")
async def call_logs(limit: int = 50, db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (
        await db.execute(
            select(CallLog).order_by(CallLog.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "direction": c.direction,
            "from": c.from_number,
            "to": c.to_number,
            "status": c.status,
            "transcript": c.transcript,
            "created_at": c.created_at.isoformat(),
        }
        for c in rows
    ]


async def _handle_webhook(provider_name: str, request: Request,
                          db: AsyncSession) -> Response:
    provider = _ADAPTERS[provider_name]()
    body = await request.body()
    form: dict[str, str] = {}
    ctype = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
        form = {k: str(v) for k, v in (await request.form()).items()}

    event = provider.parse_webhook(dict(request.headers), body, form)

    reply_text = "Hello, thank you for calling. How can I help you today?"
    if event.speech_text:
        # A live call must never receive a raw error envelope — degrade to a
        # spoken apology if the agent/LLM is unavailable.
        try:
            agent = await agent_service.ensure_default_agent(db)
            result = await agent_service.chat(
                db,
                agent=agent,
                identity=Identity(subject=f"caller:{event.from_number}",
                                  role="operator"),
                message=event.speech_text,
                channel="phone",
            )
            reply_text = result["reply"]
        except Exception:
            logger.exception("telephony agent turn failed")
            reply_text = (
                "Sorry, our assistant is temporarily unavailable. "
                "Please try again shortly."
            )

    try:
        db.add(CallLog(
            provider=event.provider,
            direction="inbound",
            from_number=event.from_number,
            to_number=event.to_number,
            status=event.event,
            transcript=event.speech_text or "",
            provider_payload=event.raw,
        ))
        await db.commit()
    except Exception:
        pass

    resp = provider.render_response(TelephonyResponse(
        say=reply_text,
        gather=event.event != "hangup",
        hangup=event.event == "hangup",
    ))
    return Response(content=resp.body, media_type=resp.content_type)


@router.post("/livekit/webhook")
async def livekit_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    return await _handle_webhook("livekit_sip", request, db)


@router.post("/twilio/webhook")
async def twilio_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    return await _handle_webhook("twilio", request, db)
