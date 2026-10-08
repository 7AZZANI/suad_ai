"""Permission engine gate behaviour (no DB required: db=None)."""

import pytest

from app.core.security import Identity
from app.permissions import permission_engine
from app.permissions.models import RiskLevel


async def _evaluate(role, scope, risk, **kw):
    return await permission_engine.evaluate(
        db=None,
        identity=Identity(subject="t", role=role),
        tool_name="t",
        required_scope=scope,
        risk_level=risk,
        arguments={},
        **kw,
    )


async def test_safe_action_allowed_with_scope():
    d = await _evaluate("operator", "tools:read", RiskLevel.SAFE)
    assert d.allowed and d.decision == "allowed"


async def test_missing_scope_denied():
    d = await _evaluate("viewer", "appointments:write", RiskLevel.APPROVAL)
    assert not d.allowed and d.decision == "denied"


async def test_blocked_never_runs():
    d = await _evaluate("admin", "tools:read", RiskLevel.BLOCKED)
    assert not d.allowed and d.decision == "blocked"


async def test_confirm_required_then_allowed():
    d1 = await _evaluate("operator", "tickets:write", RiskLevel.CONFIRM)
    assert not d1.allowed and d1.decision == "confirm_required"
    d2 = await _evaluate("operator", "tickets:write", RiskLevel.CONFIRM, confirm=True)
    assert d2.allowed


async def test_approval_required_without_db():
    d = await _evaluate("operator", "appointments:write", RiskLevel.APPROVAL)
    assert not d.allowed and d.decision == "approval_required"


async def test_admin_wildcard_auto_approves():
    d = await _evaluate("admin", "anything:write", RiskLevel.APPROVAL)
    assert d.allowed


async def test_wildcard_scope_prefix(patch_settings):
    # operator has crm:read; a crm:* tool requiring crm:read is satisfied.
    d = await _evaluate("operator", "crm:read", RiskLevel.SAFE)
    assert d.allowed


@pytest.mark.parametrize("auto", [True, False])
async def test_auto_approve_setting(patch_settings, auto):
    patch_settings(auto_approve_risky_actions=auto)
    d = await _evaluate("operator", "appointments:write", RiskLevel.APPROVAL)
    assert d.allowed is auto
