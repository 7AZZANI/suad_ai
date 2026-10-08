from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RiskLevel(StrEnum):
    """How dangerous an action is — drives the gate before execution."""

    SAFE = "safe"          # run immediately if scope granted
    CONFIRM = "confirm"    # caller must pass confirm=true
    APPROVAL = "approval"  # needs an out-of-band human approval record
    BLOCKED = "blocked"    # never executes

    @property
    def order(self) -> int:
        return ["safe", "confirm", "approval", "blocked"].index(self.value)


@dataclass
class PolicyDecision:
    allowed: bool
    decision: str  # allowed | denied | confirm_required | approval_required | blocked
    risk_level: RiskLevel
    reason: str = ""
    approval_id: str | None = None

    @property
    def needs_approval(self) -> bool:
        return self.decision == "approval_required"
