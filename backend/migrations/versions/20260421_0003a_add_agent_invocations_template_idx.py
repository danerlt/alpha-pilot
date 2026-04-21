"""add ix_agent_invocations_prompt_template_id for template-level audit queries

Revision ID: 20260421_0003a
Revises: 20260421_0003
Create Date: 2026-04-22 00:00:02.000000

Follow-up cleanup from Task 3 code review: agent_invocations is an audit log
whose common aggregations are "per-template latency / cost / token usage",
which need an index on prompt_template_id.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260421_0003a"
down_revision: Union[str, Sequence[str], None] = "20260421_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_agent_invocations_prompt_template_id",
        "agent_invocations",
        ["prompt_template_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_invocations_prompt_template_id",
        table_name="agent_invocations",
    )
