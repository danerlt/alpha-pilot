"""insight schema: experiences (v2), experience_summaries, trade_attributions, strategy_scores

Revision ID: 20260421_0004
Revises: 20260421_0003a
Create Date: 2026-04-22 00:00:03.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0004"
down_revision: Union[str, Sequence[str], None] = "20260421_0003a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "experiences",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # Fresh table — no server_default on account_id.
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("trade_id", sa.BigInteger(), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("regime_at_open", sa.String(length=20), nullable=True),
        sa.Column("strategy_mode", sa.String(length=30), nullable=True),
        sa.Column("factor_snapshot_at_open_id", sa.BigInteger(), nullable=True),
        sa.Column("pnl_pct", sa.Numeric(10, 6), nullable=True),
        sa.Column("hold_duration", sa.Integer(), nullable=True),  # seconds
        sa.Column("exit_reason", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_experiences_account"),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], name="fk_experiences_trade"),
    )

    op.create_table(
        "experience_summaries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("experience_id", sa.BigInteger(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("generated_by_agent", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["experience_id"], ["experiences.id"], name="fk_experience_summaries_experience"),
    )

    op.create_table(
        "trade_attributions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trade_id", sa.BigInteger(), nullable=False),
        sa.Column("by_symbol", sa.JSON(), nullable=True),
        sa.Column("by_time_bucket", sa.String(length=40), nullable=True),
        sa.Column("by_exit_reason", sa.String(length=30), nullable=True),
        sa.Column("by_factors_json", sa.JSON(), nullable=True),
        sa.Column("factor_contributions_json", sa.JSON(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], name="fk_trade_attributions_trade"),
    )

    op.create_table(
        "strategy_scores",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # Fresh table — no server_default on account_id.
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("strategy_mode", sa.String(length=30), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("regime", sa.String(length=20), nullable=False),
        sa.Column("window", sa.String(length=10), nullable=False),  # 7d | 30d
        sa.Column("win_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("pnl_sum", sa.Numeric(20, 8), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(10, 6), nullable=True),
        sa.Column("sharpe", sa.Numeric(8, 4), nullable=True),
        sa.Column("false_breakout_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("regime_fit_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_strategy_scores_account"),
    )
    op.create_index(
        "ix_strategy_scores_key",
        "strategy_scores",
        ["account_id", "strategy_mode", "symbol", "regime", "window"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_strategy_scores_key", table_name="strategy_scores")
    op.drop_table("strategy_scores")
    op.drop_table("trade_attributions")
    op.drop_table("experience_summaries")
    op.drop_table("experiences")
