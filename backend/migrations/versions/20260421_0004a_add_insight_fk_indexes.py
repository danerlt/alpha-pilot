"""add FK-column indexes on insight tables for common lookup patterns

Revision ID: 20260421_0004a
Revises: 20260421_0004
Create Date: 2026-04-22 00:00:04.000000

Follow-up from Task 4 code review. All three columns are foreign keys that
will be filtered on frequently:
  - experiences.trade_id: "experience for trade X"
  - experience_summaries.experience_id: "summary for experience X"
  - trade_attributions.trade_id: "attribution for trade X"

Without these indexes every filter-by-FK query is a sequential scan.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260421_0004a"
down_revision: Union[str, Sequence[str], None] = "20260421_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_experiences_trade_id", "experiences", ["trade_id"])
    op.create_index(
        "ix_experience_summaries_experience_id",
        "experience_summaries",
        ["experience_id"],
    )
    op.create_index(
        "ix_trade_attributions_trade_id",
        "trade_attributions",
        ["trade_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_trade_attributions_trade_id", table_name="trade_attributions")
    op.drop_index("ix_experience_summaries_experience_id", table_name="experience_summaries")
    op.drop_index("ix_experiences_trade_id", table_name="experiences")
