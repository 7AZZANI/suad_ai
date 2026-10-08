from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Identity, get_db, get_identity
from app.api.schemas import AgentCreate, AgentOut, ChatRequest, ChatResponse
from app.core.logging import get_logger
from app.services import agent_service

router = APIRouter(prefix="/api/agents", tags=["agents"])
logger = get_logger("app.api.agents")


@router.get("", response_model=list[AgentOut])
async def list_agents(db: AsyncSession = Depends(get_db)):
    await agent_service.ensure_default_agent(db)
    return await agent_service.list_agents(db)


@router.post("", response_model=AgentOut, status_code=201)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)):
    return await agent_service.create_agent(db, payload.model_dump())


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    return await agent_service.get_agent(db, agent_id)


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat(
    agent_id: str,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_identity),
):
    agent = await agent_service.get_agent(db, agent_id)
    return await agent_service.chat(
        db,
        agent=agent,
        identity=identity,
        message=payload.message,
        conversation_id=payload.conversation_id,
        recipe_name=payload.recipe,
        confirm=payload.confirm,
        approval_id=payload.approval_id,
    )


@router.post("/{agent_id}/voice")
async def voice(
    agent_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_identity),
):
    """STT -> agent -> TTS. Returns transcript, reply and base64 audio."""
    agent = await agent_service.get_agent(db, agent_id)
    audio = await file.read()
    return await agent_service.voice_turn(
        db, agent=agent, identity=identity, audio=audio
    )


@router.websocket("/{agent_id}/ws")
async def chat_ws(websocket: WebSocket, agent_id: str):
    """Live chat over WebSocket.

    Send JSON: {"message": "...", "conversation_id": null, "confirm": false}
    Receive JSON: the same shape as the /chat response.
    """
    await websocket.accept()
    from app.core.security import Identity as Id
    from app.db.session import get_sessionmaker

    identity = Id(subject="ws-client", role="operator")
    maker = get_sessionmaker()
    try:
        while True:
            data = await websocket.receive_json()
            try:
                async with maker() as db:
                    agent = await agent_service.get_agent(db, agent_id)
                    result = await agent_service.chat(
                        db,
                        agent=agent,
                        identity=identity,
                        message=data.get("message", ""),
                        conversation_id=data.get("conversation_id"),
                        recipe_name=data.get("recipe"),
                        confirm=bool(data.get("confirm", False)),
                        approval_id=data.get("approval_id"),
                    )
                await websocket.send_json(result)
            except Exception as exc:  # keep the socket alive on errors
                await websocket.send_json({"error": str(exc)})
    except WebSocketDisconnect:
        logger.info("ws disconnected agent=%s", agent_id)
