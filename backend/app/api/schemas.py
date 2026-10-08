from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    recipe: str | None = None
    confirm: bool = False
    approval_id: str | None = None


class ChatResponse(BaseModel):
    agent_id: str
    conversation_id: str | None
    reply: str
    tool_invocations: list[dict[str, Any]] = []
    pending_action: dict[str, Any] | None = None
    used_rag: bool = False
    citations: list[dict[str, Any]] = []


class AgentCreate(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = "You are a helpful assistant."
    role: str = "operator"
    allowed_tools: str = "*"
    temperature: float = 0.3
    max_tokens: int = 1024
    rag_enabled: bool = True


class AgentOut(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    role: str
    allowed_tools: str
    temperature: float
    max_tokens: int
    rag_enabled: bool
    is_active: bool

    model_config = {"from_attributes": True}


class RoleUpsert(BaseModel):
    name: str
    description: str = ""
    scopes: list[str] = []


class IngestRequest(BaseModel):
    title: str
    text: str = Field(min_length=1)
    source: str = "api"


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = 4


class ApprovalDecision(BaseModel):
    approve: bool
    decided_by: str = "admin"
