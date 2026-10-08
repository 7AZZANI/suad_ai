from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import ApprovalDecision, RoleUpsert
from app.core.errors import NotFoundError
from app.db.models import ApprovalRequest, AuditLog, Role
from app.permissions.defaults import DEFAULT_ROLES
from app.tools.registry import registry

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@router.get("/tools")
async def list_tools() -> list[dict]:
    """Every registered tool with its scope + risk level (transparency)."""
    return [
        {
            "name": t.name,
            "description": t.description,
            "scope": t.scope,
            "risk_level": t.risk_level.value,
            "parameters": t.parameters,
        }
        for t in registry.all()
    ]


@router.get("/roles")
async def list_roles(db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (await db.execute(select(Role))).scalars().all()
    if rows:
        return [{"name": r.name, "description": r.description, "scopes": r.scopes}
                for r in rows]
    return [{"name": n, "description": c["description"], "scopes": c["scopes"]}
            for n, c in DEFAULT_ROLES.items()]


@router.put("/roles")
async def upsert_role(payload: RoleUpsert, db: AsyncSession = Depends(get_db)) -> dict:
    role = (
        await db.execute(select(Role).where(Role.name == payload.name))
    ).scalar_one_or_none()
    if role is None:
        role = Role(name=payload.name)
        db.add(role)
    role.description = payload.description
    role.scopes = payload.scopes
    await db.commit()
    return {"name": role.name, "description": role.description, "scopes": role.scopes}


@router.get("/audit")
async def audit_logs(limit: int = 100, db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (
        await db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "subject": r.subject,
            "role": r.role,
            "tool": r.tool_name,
            "risk_level": r.risk_level,
            "decision": r.decision,
            "success": r.success,
            "summary": r.result_summary,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/approvals")
async def approvals(status: str = "pending",
                    db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (
        await db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.status == status)
            .order_by(ApprovalRequest.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "tool": r.tool_name,
            "subject": r.subject,
            "role": r.role,
            "arguments": r.arguments,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/approvals/{approval_id}")
async def decide_approval(
    approval_id: str,
    decision: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
) -> dict:
    req = (
        await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
        )
    ).scalar_one_or_none()
    if req is None:
        raise NotFoundError("Approval request not found.")
    req.status = "approved" if decision.approve else "rejected"
    req.decided_by = decision.decided_by
    await db.commit()
    return {"id": req.id, "status": req.status}
