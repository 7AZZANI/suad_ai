"""Built-in roles and their scopes.

These are seeded into the `roles` table but the engine also falls back to
them if the DB is unavailable, so permission checks never fail open.
"""

from __future__ import annotations

DEFAULT_ROLES: dict[str, dict] = {
    "admin": {
        "description": "Full access including approval-tier actions.",
        "scopes": ["*"],
    },
    "operator": {
        "description": "Day-to-day agent operation; risky actions need approval.",
        "scopes": [
            "tools:read",
            "knowledge:read",
            "crm:read",
            "tickets:write",
            "appointments:write",
            "handoff:write",
        ],
    },
    "viewer": {
        "description": "Read-only: chat and knowledge lookup, no writes.",
        "scopes": ["tools:read", "knowledge:read", "crm:read"],
    },
}


def scopes_for(role: str) -> set[str]:
    return set(DEFAULT_ROLES.get(role, DEFAULT_ROLES["viewer"])["scopes"])


def scope_satisfied(granted: set[str], required: str) -> bool:
    if "*" in granted or not required:
        return True
    if required in granted:
        return True
    # Wildcard prefix support: "crm:*" grants "crm:read".
    prefix = required.split(":", 1)[0] + ":*"
    return prefix in granted
