"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

_ts = sa.func.now()


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_ts, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_ts, nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default="You are helpful."),
        sa.Column("role", sa.String(64), nullable=False, server_default="operator"),
        sa.Column("allowed_tools", sa.Text(), nullable=False, server_default="*"),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="1024"),
        sa.Column("rag_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index("ix_agents_name", "agents", ["name"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False, server_default="chat"),
        sa.Column("subject", sa.String(120), nullable=False, server_default="anonymous"),
        *_timestamps(),
    )
    op.create_index("ix_conversations_agent_id", "conversations", ["agent_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"),
                  nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("tool_name", sa.String(64), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject", sa.String(128), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("agent_id", sa.String(36), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_audit_logs_subject", "audit_logs", ["subject"])
    op.create_index("ix_audit_logs_tool_name", "audit_logs", ["tool_name"])

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(128), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("decided_by", sa.String(128), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_approval_requests_tool_name", "approval_requests", ["tool_name"])

    op.create_table(
        "call_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False, server_default="inbound"),
        sa.Column("from_number", sa.String(40), nullable=False, server_default=""),
        sa.Column("to_number", sa.String(40), nullable=False, server_default=""),
        sa.Column("status", sa.String(24), nullable=False, server_default="received"),
        sa.Column("agent_id", sa.String(36), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=False, server_default=""),
        sa.Column("provider_payload", sa.JSON(), nullable=False, server_default="{}"),
        *_timestamps(),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source", sa.String(255), nullable=False, server_default="upload"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="ingested"),
        sa.Column("preview", sa.Text(), nullable=False, server_default=""),
        *_timestamps(),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("scopes", sa.JSON(), nullable=False, server_default="[]"),
        *_timestamps(),
    )
    op.create_index("ix_roles_name", "roles", ["name"])


def downgrade() -> None:
    for table in (
        "roles", "documents", "call_logs", "approval_requests",
        "audit_logs", "messages", "conversations", "agents",
    ):
        op.drop_table(table)
