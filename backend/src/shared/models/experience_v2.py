from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class ExperienceV2(Base, TimestampMixin):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Fresh table — NO Python default on account_id.
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), nullable=False
    )
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    trade_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("trades.id"))
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    regime_at_open: Mapped[str | None] = mapped_column(String(20))
    strategy_mode: Mapped[str | None] = mapped_column(String(30))
    factor_snapshot_at_open_id: Mapped[int | None] = mapped_column(BigInteger)
    pnl_pct: Mapped[float | None] = mapped_column(Numeric(10, 6))
    hold_duration: Mapped[int | None] = mapped_column(Integer)
    exit_reason: Mapped[str | None] = mapped_column(String(30))


class ExperienceSummary(Base, TimestampMixin):
    __tablename__ = "experience_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    experience_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("experiences.id"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[dict | None] = mapped_column(JSON)
    generated_by_agent: Mapped[str | None] = mapped_column(String(40))
