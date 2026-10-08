"""Permission engine — the single gate before any tool runs.

Flow per tool call:
  1. resolve the caller's granted scopes (DB role, fallback to defaults)
  2. check the tool's required scope
  3. apply the tool's risk level (safe / confirm / approval / blocked)
  4. write an immutable audit log of the decision

Nothing executes a tool without passing through :meth:`evaluate`.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import Identity
from app.db.models import ApprovalRequest, AuditLog, Role
from app.permissions.defaults import scope_satisfied, scopes_for
from app.permissions.models import PolicyDecision, RiskLevel

logger = get_logger("app.permissions")


class PermissionEngine:
    async def granted_scopes(self, db: AsyncSession | None, role: str) -> set[str]:
        if db is not None:
            try:
                row = (
                    await db.execute(select(Role).where(Role.name == role))
                ).scalar_one_or_none()
                if row:
                    return set(row.scopes)
            except Exception:  # pragma: no cover - DB optional
                logger.warning("role lookup failed; using defaults role=%s", role)
        return scopes_for(role)

    async def evaluate(
        self,
        *,
        db: AsyncSession | None,
        identity: Identity,
        tool_name: str,
        required_scope: str,
        risk_level: RiskLevel,
        arguments: dict[str, Any],
        confirm: bool = False,
        approval_id: str | None = None,
        agent_id: str | None = None,
    ) -> PolicyDecision:
        scopes = await self.granted_scopes(db, identity.role)

        if risk_level == RiskLevel.BLOCKED:
            decision = PolicyDecision(False, "blocked", risk_level,
                                      "Tool is blocked by policy.")
        elif not scope_satisfied(scopes, required_scope):
            decision = PolicyDecision(
                False, "denied", risk_level,
                f"Role '{identity.role}' lacks scope '{required_scope}'.",
            )
        elif risk_level == RiskLevel.SAFE:
            decision = PolicyDecision(True, "allowed", risk_level, "Safe action.")
        elif risk_level == RiskLevel.CONFIRM:
            decision = (
                PolicyDecision(True, "allowed", risk_level, "Confirmed by caller.")
                if confirm
                else PolicyDecision(False, "confirm_required", risk_level,
                                    "Pass confirm=true to proceed.")
            )
        else:  # APPROVAL
            decision = await self._evaluate_approval(
                db, identity, tool_name, arguments, approval_id, scopes
            )

        await self._audit(db, identity, tool_name, risk_level, decision,
                           arguments, agent_id)
        logger.info(
            "policy tool=%s role=%s decision=%s", tool_name, identity.role,
            decision.decision,
        )
        return decision

    async def _evaluate_approval(
        self,
        db: AsyncSession | None,
        identity: Identity,
        tool_name: str,
        arguments: dict[str, Any],
        approval_id: str | None,
        scopes: set[str],
    ) -> PolicyDecision:
        if settings.auto_approve_risky_actions or "*" in scopes:
            return PolicyDecision(True, "allowed", RiskLevel.APPROVAL,
                                  "Auto-approved (admin/dev).")
        if approval_id and db is not None:
            req = (
                await db.execute(
                    select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
                )
            ).scalar_one_or_none()
            if req and req.status == "approved" and req.tool_name == tool_name:
                return PolicyDecision(True, "allowed", RiskLevel.APPROVAL,
                                      "Approved by human.", approval_id=approval_id)
            return PolicyDecision(False, "approval_required", RiskLevel.APPROVAL,
                                  "Approval not granted yet.", approval_id=approval_id)
        # Create a pending approval request the admin UI can act on.
        new_id = None
        if db is not None:
            req = ApprovalRequest(
                tool_name=tool_name,
                subject=identity.subject,
                role=identity.role,
                arguments=arguments,
                status="pending",
                reason="Risky action awaiting human approval.",
            )
            db.add(req)
            await db.flush()
            new_id = req.id
            await db.commit()
        return PolicyDecision(False, "approval_required", RiskLevel.APPROVAL,
                              "Human approval required.", approval_id=new_id)

    async def _audit(
        self,
        db: AsyncSession | None,
        identity: Identity,
        tool_name: str,
        risk_level: RiskLevel,
        decision: PolicyDecision,
        arguments: dict[str, Any],
        agent_id: str | None,
    ) -> None:
        if db is None:
            return
        try:
            db.add(
                AuditLog(
                    subject=identity.subject,
                    role=identity.role,
                    tool_name=tool_name,
                    risk_level=risk_level.value,
                    decision=decision.decision,
                    arguments=arguments,
                    success=decision.allowed,
                    result_summary=decision.reason,
                    agent_id=agent_id,
                )
            )
            await db.commit()
        except Exception:  # pragma: no cover - auditing must not break calls
            logger.warning("audit write failed tool=%s", tool_name)


permission_engine = PermissionEngine()
