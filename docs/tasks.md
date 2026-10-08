# Task recipes & business tools

## Task recipes

A recipe is a declarative playbook in `backend/app/tasks/recipes/*.yaml`. It is
loaded at request time (edit → no restart) and injected into the agent's
system prompt: title, guidance and ordered steps, plus the tools it expects.

Shipped recipes:

| Name | Purpose |
|---|---|
| `customer_support_ticket` | KB lookup first, then open a ticket |
| `appointment_booking` | Collect details, book (approval-tier) |
| `order_status_lookup` | Look up an order by ID |
| `faq_answering` | Answer strictly from the knowledge base |
| `human_handoff` | Clean escalation to a person |

Recipe schema:

```yaml
title: Order Status Lookup
description: Tell a customer the current status of their order.
tools: [order_status_lookup, human_handoff]
guidance: >
  Ask for the order ID, look it up, explain status and ETA. Never guess.
steps:
  - Ask for the order ID.
  - Call order_status_lookup with the ID.
  - Report status, carrier and ETA.
  - If not found, apologize and offer human_handoff.
```

Use a recipe via the Playground dropdown or the API:

```bash
curl -X POST http://localhost:8000/api/agents/default/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"order 1001?","recipe":"order_status_lookup"}'
```

List/inspect: `GET /api/tasks`, `GET /api/tasks/{name}`.

## Adding a business tool

Tools live in `app/tools/builtin.py`. Each tool declares a JSON schema, a
permission **scope** and a **risk level**. The LLM only ever *requests* a tool;
the runtime validates + gates + audits before the handler runs.

```python
from app.permissions.models import RiskLevel
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.registry import registry

async def _refund(ctx: ToolContext, args: dict) -> ToolResult:
    # ctx.identity / ctx.db are provided. Use typed accessors only —
    # never build SQL from `args`. See app/tools/db_safe.py.
    amount = float(args["amount"])
    return ToolResult(True, {"refunded": amount}, f"Refunded {amount}.")

registry.register(Tool(
    name="issue_refund",
    description="Issue a refund to a customer.",
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string"},
                        "amount": {"type": "number"}},
        "required": ["order_id", "amount"],
    },
    handler=_refund,
    scope="billing:write",       # role must grant this scope
    risk_level=RiskLevel.APPROVAL,  # money → human approval
))
```

Then grant `billing:write` to a role (Permissions page or `PUT
/api/permissions/roles`) and reference `issue_refund` in a recipe's `tools`.

### The no-raw-SQL rule

The model never sees or writes SQL. Handlers call **named, typed functions**
in `app/tools/db_safe.py` which use parameterized SQLAlchemy queries. The demo
order/ticket stores there are in-memory stand-ins — replace the function
bodies with your real CRM/OMS; the tool/permission layers don't change.
