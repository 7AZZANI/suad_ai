"""Setup Wizard endpoints — probe each provider independently."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.services import setup_service

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/summary")
async def summary() -> dict:
    """Non-secret view of the active configuration."""
    return settings.public_summary()


@router.post("/test-llm")
async def test_llm() -> dict:
    return await setup_service.test_llm()


@router.post("/test-stt")
async def test_stt() -> dict:
    return await setup_service.test_stt()


@router.post("/test-tts")
async def test_tts() -> dict:
    return await setup_service.test_tts()


@router.post("/test-database")
async def test_database() -> dict:
    return await setup_service.test_database()


@router.post("/test-qdrant")
async def test_qdrant() -> dict:
    return await setup_service.test_memory()


@router.post("/test-telephony")
async def test_telephony() -> dict:
    return await setup_service.test_telephony()


@router.post("/test-all")
async def test_all() -> dict:
    return await setup_service.run_all()
