"""shadow_ops_schema

Revision ID: d9076875486b
Revises: 20260421_0004a
Create Date: 2026-04-23 20:01:26.267214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9076875486b'
down_revision: Union[str, None] = '20260421_0004a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "shadow_decisions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shadow_run_id", sa.String(length=64), nullable=False),
        sa.Column("real_decision_id", sa.BigInteger(), nullable=True),
        sa.Column("proposal_json", sa.JSON(), nullable=False),
        sa.Column("parameter_version_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["real_decision_id"], ["ai_decisions.id"], name="fk_shadow_decisions_real"),
        sa.ForeignKeyConstraint(["parameter_version_id"], ["parameter_versions.id"], name="fk_shadow_decisions_param"),
    )
    op.create_index(
        "ix_shadow_decisions_shadow_run_id",
        "shadow_decisions",
        ["shadow_run_id"],
    )

    op.create_table(
        "shadow_evaluations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shadow_decision_id", sa.BigInteger(), nullable=False),
        sa.Column("real_trade_id", sa.BigInteger(), nullable=True),
        sa.Column("shadow_pnl_sim", sa.Numeric(20, 8), nullable=True),
        sa.Column("real_pnl", sa.Numeric(20, 8), nullable=True),
        sa.Column("diff", sa.Numeric(20, 8), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["shadow_decision_id"], ["shadow_decisions.id"], name="fk_shadow_evaluations_shadow"),
        sa.ForeignKeyConstraint(["real_trade_id"], ["trades.id"], name="fk_shadow_evaluations_real"),
    )
    op.create_index(
        "ix_shadow_evaluations_shadow_decision_id",
        "shadow_evaluations",
        ["shadow_decision_id"],
    )

    op.create_table(
        "ops_diagnoses",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("triggered_by_event_id", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("pattern_matched", sa.String(length=100), nullable=True),
        sa.Column("llm_narrative", sa.Text(), nullable=True),
        sa.Column("recommendations_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )


def downgrade() -> None:
    op.drop_table("ops_diagnoses")
    op.drop_index("ix_shadow_evaluations_shadow_decision_id", table_name="shadow_evaluations")
    op.drop_table("shadow_evaluations")
    op.drop_index("ix_shadow_decisions_shadow_run_id", table_name="shadow_decisions")
    op.drop_table("shadow_decisions")
