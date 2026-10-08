# Permissions

The permission engine (`app/permissions/policy.py`) is the **single gate**
every tool call passes before execution. No code path runs a tool without it.

## Model

- **Identity** — `Identity(subject, role)`. Resolved from request headers
  (`X-API-Key`, `X-Role`) today; replace `app/core/security.get_identity`
  with OIDC/JWT later — nothing downstream changes.
- **Role → scopes** — a role grants a set of scope strings. Defaults live in
  `app/permissions/defaults.py` and are seeded into the `roles` table; the DB
  can override/extend them at runtime. If the DB is unavailable the defaults
  are used (the gate never fails open).
- **Scope** — each tool requires one scope, e.g. `crm:read`,
  `appointments:write`. `*` grants everything; `crm:*` grants `crm:read` etc.
- **Risk level** — per tool:

  | Level | Behaviour |
  |---|---|
  | `safe` | Runs immediately (if scope granted). |
  | `confirm` | Requires `confirm=true` from the caller. |
  | `approval` | Creates a pending `ApprovalRequest`; a human approves it out of band, then the call is retried with `approval_id`. |
  | `blocked` | Never runs. |

- **Audit** — every decision (allowed/denied/confirm/approval) is written to
  the immutable `audit_logs` table with subject, role, tool, args, outcome.

## Default roles

| Role | Scopes |
|---|---|
| `admin` | `*` (all; auto-approves `approval` tier) |
| `operator` | `tools:read`, `knowledge:read`, `crm:read`, `tickets:write`, `appointments:write`, `handoff:write` |
| `viewer` | `tools:read`, `knowledge:read`, `crm:read` (read-only) |

## Flow

```
LLM requests tool ─▶ registry.get(tool) ─▶ PermissionEngine.evaluate(
        identity, required_scope, risk_level, args, confirm, approval_id)
   ├─ scope not granted        ─▶ denied   (audited)
   ├─ risk=blocked             ─▶ blocked  (audited)
   ├─ risk=safe                ─▶ allowed  ─▶ handler runs
   ├─ risk=confirm & !confirm  ─▶ confirm_required  (UI shows a button)
   └─ risk=approval            ─▶ approval_required + ApprovalRequest row
```

## Approving a risky action

1. Agent calls e.g. `book_appointment` (`approval` tier) → response contains
   `pending_action` with an `approval_id`.
2. An admin approves it: **Permissions page**, or
   `POST /api/permissions/approvals/{id}` `{"approve": true}`.
3. Re-send the chat with `approval_id` (the Playground's *Confirm & retry*
   button does this) → the tool now executes.

`AUTO_APPROVE_RISKY_ACTIONS=true` bypasses step 2 — **development only**.

## Why the LLM can't escalate

- The LLM emits *tool requests*, not code or SQL.
- Tool args are validated against a JSON schema.
- Scope + risk are properties of the **tool definition**, not of the model
  output — the model cannot change its own permissions.
- Handlers touch data only via typed `db_safe` functions (parameterized).
- Everything is audited, so misuse is observable.

Inspect live: `GET /api/permissions/tools`, `/roles`, `/audit`, `/approvals`.
