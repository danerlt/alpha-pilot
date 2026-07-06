"""lab_candidates table

Revision ID: 99ca505e8d31
Revises: 3970b9376189
Create Date: 2026-07-06 10:06:20.949580

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '99ca505e8d31'
down_revision: Union[str, None] = '3970b9376189'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lab_candidates",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("params_json", sa.JSON(), nullable=False),
        sa.Column("stage", sa.String(length=20), nullable=False),
        sa.Column("shadow_run_id", sa.String(length=64), nullable=True),
        sa.Column("shadow_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shadow_days_target", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("promoted_by", sa.BigInteger(), nullable=True),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rollback_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("enable_flag", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column("delete_flag", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
    )
    op.create_index("ix_lab_candidates_stage", "lab_candidates", ["stage"])
    op.create_index("ix_lab_candidates_shadow_run_id", "lab_candidates", ["shadow_run_id"])


def downgrade() -> None:
    op.drop_index("ix_lab_candidates_shadow_run_id", table_name="lab_candidates")
    op.drop_index("ix_lab_candidates_stage", table_name="lab_candidates")
    op.drop_table("lab_candidates")
