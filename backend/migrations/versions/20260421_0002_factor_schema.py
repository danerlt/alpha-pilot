"""factor layer schema: factor_definitions, factor_snapshots, factor_candidates

Revision ID: 20260421_0002
Revises: 20260421_0001
Create Date: 2026-04-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0002"
down_revision: Union[str, Sequence[str], None] = "20260421_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "factor_definitions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("inputs_json", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("formula_code_ref", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    op.create_index("ix_factor_definitions_name_version", "factor_definitions", ["name", "version"], unique=True)

    op.create_table(
        "factor_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # Fresh table — no server_default on account_id (per Task 1 pattern).
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("factors_json", sa.JSON(), nullable=False),
        sa.Column("factor_def_versions_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_factor_snapshots_account"),
    )
    op.create_index(
        "ix_factor_snapshots_unique",
        "factor_snapshots",
        ["account_id", "trading_mode", "symbol", "timeframe", "open_time"],
        unique=True,
    )

    op.create_table(
        "factor_candidates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("proposed_by_agent", sa.String(length=40), nullable=False, server_default="factor_ai"),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("formula_code_ref", sa.String(length=200), nullable=True),
        sa.Column("validation_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("validation_report_json", sa.JSON(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )


def downgrade() -> None:
    op.drop_table("factor_candidates")
    op.drop_index("ix_factor_snapshots_unique", table_name="factor_snapshots")
    op.drop_table("factor_snapshots")
    op.drop_index("ix_factor_definitions_name_version", table_name="factor_definitions")
    op.drop_table("factor_definitions")
