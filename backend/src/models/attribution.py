from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, BigIntPk


class TradeAttribution(Base):
    __tablename__ = "trade_attributions"

    __table_args__ = (
        Index("ix_trade_attributions_trade_id", "trade_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    trade_id: Mapped[int] = mapped_column(nullable=False)
    by_symbol: Mapped[dict | None] = mapped_column(JSON)
    by_time_bucket: Mapped[str | None] = mapped_column(String(40))
    by_exit_reason: Mapped[str | None] = mapped_column(String(30))
    by_factors_json: Mapped[dict | None] = mapped_column(JSON)
    factor_contributions_json: Mapped[dict | None] = mapped_column(JSON)
    narrative: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StrategyScore(Base):
    __tablename__ = "strategy_scores"

    __table_args__ = (
        Index(
            "ix_strategy_scores_key",
            "account_id", "strategy_mode", "symbol", "regime", "window",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    # Fresh table — NO Python default on account_id.
    account_id: Mapped[int] = mapped_column(
        nullable=False
    )
    strategy_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    regime: Mapped[str] = mapped_column(String(20), nullable=False)
    window: Mapped[str] = mapped_column(String(10), nullable=False)
    win_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    pnl_sum: Mapped[float | None] = mapped_column(Numeric(20, 8))
    max_drawdown: Mapped[float | None] = mapped_column(Numeric(10, 6))
    sharpe: Mapped[float | None] = mapped_column(Numeric(8, 4))
    false_breakout_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    regime_fit_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
