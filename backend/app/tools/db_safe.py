"""Safe, typed data accessors used by tools.

This is the ONLY place tools read/write business data. Rules enforced here:
  * The LLM never supplies SQL. Tools call these named functions.
  * Queries are parameterized via SQLAlchemy Core (no string interpolation).
  * Each function returns a typed dict, never a raw cursor.

The order/ticket stores below are in-memory demo stand-ins. Replace the
bodies with calls into your real CRM/OMS — the tool layer and permission
model do not change.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

# --- Demo data (swap for real integrations) --------------------------------
_DEMO_ORDERS: dict[str, dict[str, Any]] = {
    "1001": {"status": "shipped", "carrier": "DHL", "eta": "2026-05-21"},
    "1002": {"status": "processing", "carrier": None, "eta": "2026-05-25"},
    "1003": {"status": "delivered", "carrier": "UPS", "eta": "2026-05-15"},
}
_TICKETS: list[dict[str, Any]] = []
_APPOINTMENTS: list[dict[str, Any]] = []


def get_order_status(order_id: str) -> dict[str, Any] | None:
    """Look up an order by id. Returns None if not found."""
    order = _DEMO_ORDERS.get(str(order_id).strip())
    if not order:
        return None
    return {"order_id": str(order_id), **order}


def create_support_ticket(*, customer: str, subject: str, body: str,
                           priority: str = "normal") -> dict[str, Any]:
    ticket = {
        "ticket_id": "TK-" + uuid.uuid4().hex[:8].upper(),
        "customer": customer,
        "subject": subject,
        "body": body,
        "priority": priority if priority in {"low", "normal", "high"} else "normal",
        "status": "open",
        "created_at": datetime.now(UTC).isoformat(),
    }
    _TICKETS.append(ticket)
    return ticket


def book_appointment(*, customer: str, service: str, when: str) -> dict[str, Any]:
    appt = {
        "appointment_id": "AP-" + uuid.uuid4().hex[:8].upper(),
        "customer": customer,
        "service": service,
        "when": when,
        "status": "booked",
    }
    _APPOINTMENTS.append(appt)
    return appt


def list_tickets() -> list[dict[str, Any]]:
    return list(_TICKETS)


# Example of the SAFE parameterized DB pattern for real tables:
#
#   from sqlalchemy import select
#   async def get_customer(db, customer_id: str):
#       row = (await db.execute(
#           select(Customer).where(Customer.id == customer_id)  # parameterized
#       )).scalar_one_or_none()
#       return _serialize(row)
