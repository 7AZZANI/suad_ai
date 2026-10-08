"""Built-in business tools.

Each tool declares a permission ``scope`` and a ``risk_level``. The runtime
enforces these before the handler runs — see app/permissions/policy.py.
Import this module once at startup to populate the registry.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.permissions.models import RiskLevel
from app.providers.memory import get_memory
from app.tools import db_safe
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.registry import registry


async def _now(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    return ToolResult(True, {"utc": datetime.now(UTC).isoformat()},
                       "Current UTC time.")


async def _order_status(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    order = db_safe.get_order_status(str(args.get("order_id", "")))
    if not order:
        return ToolResult(False, None, "Order not found.")
    return ToolResult(True, order, f"Order {order['order_id']} is {order['status']}.")


async def _knowledge_search(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    memory = get_memory()
    if not memory.enabled:
        return ToolResult(True, [], "Knowledge base disabled (RAG off).")
    chunks = await memory.search(str(args.get("query", "")),
                                 k=int(args.get("k", 4)))
    return ToolResult(
        True,
        [{"text": c.text, "score": c.score, "metadata": c.metadata} for c in chunks],
        f"Found {len(chunks)} passages.",
    )


async def _create_ticket(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    ticket = db_safe.create_support_ticket(
        customer=str(args.get("customer", ctx.identity.subject)),
        subject=str(args.get("subject", "")),
        body=str(args.get("body", "")),
        priority=str(args.get("priority", "normal")),
    )
    return ToolResult(True, ticket, f"Created ticket {ticket['ticket_id']}.")


async def _book_appointment(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    appt = db_safe.book_appointment(
        customer=str(args.get("customer", ctx.identity.subject)),
        service=str(args.get("service", "")),
        when=str(args.get("when", "")),
    )
    return ToolResult(True, appt, f"Booked {appt['appointment_id']}.")


async def _human_handoff(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        True,
        {"handoff": True, "reason": args.get("reason", "customer requested")},
        "Escalated to a human agent.",
    )


def register_builtin_tools() -> None:
    if registry.all():  # idempotent
        return
    registry.register(Tool(
        name="get_current_time",
        description="Get the current UTC time.",
        parameters={"type": "object", "properties": {}},
        handler=_now,
        scope="tools:read",
        risk_level=RiskLevel.SAFE,
    ))
    registry.register(Tool(
        name="order_status_lookup",
        description="Look up the status of a customer order by its ID.",
        parameters={
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
        handler=_order_status,
        scope="crm:read",
        risk_level=RiskLevel.SAFE,
    ))
    registry.register(Tool(
        name="knowledge_search",
        description="Search the business knowledge base for relevant information.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 4},
            },
            "required": ["query"],
        },
        handler=_knowledge_search,
        scope="knowledge:read",
        risk_level=RiskLevel.SAFE,
    ))
    registry.register(Tool(
        name="create_support_ticket",
        description="Create a customer support ticket.",
        parameters={
            "type": "object",
            "properties": {
                "customer": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
            },
            "required": ["subject", "body"],
        },
        handler=_create_ticket,
        scope="tickets:write",
        risk_level=RiskLevel.CONFIRM,
    ))
    registry.register(Tool(
        name="book_appointment",
        description="Book an appointment for a customer (requires approval).",
        parameters={
            "type": "object",
            "properties": {
                "customer": {"type": "string"},
                "service": {"type": "string"},
                "when": {"type": "string", "description": "ISO datetime"},
            },
            "required": ["service", "when"],
        },
        handler=_book_appointment,
        scope="appointments:write",
        risk_level=RiskLevel.APPROVAL,
    ))
    registry.register(Tool(
        name="human_handoff",
        description="Escalate the conversation to a human agent.",
        parameters={
            "type": "object",
            "properties": {"reason": {"type": "string"}},
        },
        handler=_human_handoff,
        scope="handoff:write",
        risk_level=RiskLevel.SAFE,
    ))
