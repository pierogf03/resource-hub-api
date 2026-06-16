"""ai chat audit logs

Revision ID: 002
Revises: 001
Create Date: 2026-06-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_chat_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("reply", sa.Text(), nullable=True),
        sa.Column("intent", sa.String(length=100), nullable=True),
        sa.Column("used_skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("action_id", sa.String(length=255), nullable=True),
        sa.Column("action_type", sa.String(length=100), nullable=True),
        sa.Column("payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("result", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_chat_audit_logs_conversation_id", "ai_chat_audit_logs", ["conversation_id"])
    op.create_index("ix_ai_chat_audit_logs_action_id", "ai_chat_audit_logs", ["action_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_chat_audit_logs_action_id", table_name="ai_chat_audit_logs")
    op.drop_index("ix_ai_chat_audit_logs_conversation_id", table_name="ai_chat_audit_logs")
    op.drop_table("ai_chat_audit_logs")
