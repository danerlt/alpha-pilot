"""init schema

Revision ID: 20260316_0001
Revises:
Create Date: 2026-03-16 00:01:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260316_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRADING_MODE_DEFAULT = "testnet"
UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "account_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_balance_usdt", sa.Numeric(20, 8), nullable=False),
        sa.Column("available_balance_usdt", sa.Numeric(20, 8), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("daily_pnl", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("daily_pnl_pct", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "ai_decisions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("entry_type", sa.String(length=10), nullable=True),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("stop_loss", sa.Numeric(20, 8), nullable=True),
        sa.Column("take_profit", sa.Numeric(20, 8), nullable=True),
        sa.Column("position_size_pct", sa.Numeric(5, 4), nullable=True),
        sa.Column("strategy_mode", sa.String(length=30), nullable=True),
        sa.Column("reasoning", sa.JSON(), nullable=True),
        sa.Column("risk_note", sa.Text(), nullable=True),
        sa.Column("prompt_input", sa.JSON(), nullable=True),
        sa.Column("raw_output", sa.Text(), nullable=True),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "candles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(20, 8), nullable=False),
        sa.Column("high", sa.Numeric(20, 8), nullable=False),
        sa.Column("low", sa.Numeric(20, 8), nullable=False),
        sa.Column("close", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(30, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    op.create_index(
        "ix_candles_symbol_timeframe_open_time",
        "candles",
        ["symbol", "timeframe", "open_time"],
        unique=True,
    )

    op.create_table(
        "daily_reports",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("total_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("winning_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("losing_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("win_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("total_pnl", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("total_pnl_pct", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("max_single_loss", sa.Numeric(20, 8), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(20, 8), nullable=True),
        sa.Column("risk_events_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "experience_store",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("trade_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("regime", sa.String(length=20), nullable=False),
        sa.Column("strategy_mode", sa.String(length=30), nullable=False),
        sa.Column("indicator_snapshot", sa.JSON(), nullable=True),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("exit_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("pnl", sa.Numeric(20, 8), nullable=False),
        sa.Column("pnl_pct", sa.Numeric(10, 6), nullable=False),
        sa.Column("exit_reason", sa.String(length=30), nullable=False),
        sa.Column("holding_seconds", sa.BigInteger(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "indicator_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ema20", sa.Numeric(20, 8), nullable=True),
        sa.Column("ema50", sa.Numeric(20, 8), nullable=True),
        sa.Column("ema200", sa.Numeric(20, 8), nullable=True),
        sa.Column("rsi", sa.Numeric(10, 4), nullable=True),
        sa.Column("macd", sa.Numeric(20, 8), nullable=True),
        sa.Column("macd_signal", sa.Numeric(20, 8), nullable=True),
        sa.Column("macd_hist", sa.Numeric(20, 8), nullable=True),
        sa.Column("atr", sa.Numeric(20, 8), nullable=True),
        sa.Column("bb_upper", sa.Numeric(20, 8), nullable=True),
        sa.Column("bb_middle", sa.Numeric(20, 8), nullable=True),
        sa.Column("bb_lower", sa.Numeric(20, 8), nullable=True),
        sa.Column("volume_ma", sa.Numeric(30, 8), nullable=True),
        sa.Column("volatility", sa.Numeric(10, 6), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("trace_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("binance_order_id", sa.String(length=50), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=True),
        sa.Column("filled_quantity", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("avg_fill_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("position_id", sa.BigInteger(), nullable=True),
        sa.Column("ai_decision_id", sa.BigInteger(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="OPEN"),
        sa.Column("side", sa.String(length=10), nullable=False, server_default="LONG"),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("stop_loss", sa.Numeric(20, 8), nullable=False),
        sa.Column("take_profit", sa.Numeric(20, 8), nullable=True),
        sa.Column("current_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(20, 8), nullable=True),
        sa.Column("unrealized_pnl_pct", sa.Numeric(10, 6), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_decision_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "regime_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("regime", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "risk_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("position_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default=TRADING_MODE_DEFAULT),
        sa.Column("position_id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False, server_default="LONG"),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("exit_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("pnl", sa.Numeric(20, 8), nullable=False),
        sa.Column("pnl_pct", sa.Numeric(10, 6), nullable=False),
        sa.Column("exit_reason", sa.String(length=30), nullable=False),
        sa.Column("strategy_mode", sa.String(length=30), nullable=True),
        sa.Column("regime", sa.String(length=20), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("holding_seconds", sa.BigInteger(), nullable=True),
        sa.Column("ai_decision_id", sa.BigInteger(), nullable=True),
        sa.Column("open_order_id", sa.BigInteger(), nullable=True),
        sa.Column("close_order_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )


def downgrade() -> None:
    op.drop_table("trades")
    op.drop_table("risk_events")
    op.drop_table("regime_snapshots")
    op.drop_table("positions")
    op.drop_table("orders")
    op.drop_table("indicator_snapshots")
    op.drop_table("experience_store")
    op.drop_table("daily_reports")
    op.drop_index("ix_candles_symbol_timeframe_open_time", table_name="candles")
    op.drop_table("candles")
    op.drop_table("ai_decisions")
    op.drop_table("account_snapshots")
