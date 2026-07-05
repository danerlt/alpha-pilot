"""agent_pending_actions table

Revision ID: dab932bf4b22
Revises: 6e79e5d8e1f6
Create Date: 2026-07-05 20:44:28.824957

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'dab932bf4b22'
down_revision: Union[str, None] = '6e79e5d8e1f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_pending_actions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("invocation_id", sa.BigInteger(), nullable=True),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_by", sa.BigInteger(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("enable_flag", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column("delete_flag", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
    )
    op.create_index("ix_agent_pending_actions_invocation_id", "agent_pending_actions", ["invocation_id"])
    op.create_index("ix_agent_pending_actions_status", "agent_pending_actions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_agent_pending_actions_status", table_name="agent_pending_actions")
    op.drop_index("ix_agent_pending_actions_invocation_id", table_name="agent_pending_actions")
    op.drop_table("agent_pending_actions")
