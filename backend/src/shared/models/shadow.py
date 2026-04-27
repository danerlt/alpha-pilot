from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, BigIntPk, TimestampMixin


class ShadowDecision(Base, TimestampMixin):
    __tablename__ = "shadow_decisions"

    __table_args__ = (
        Index("ix_shadow_decisions_shadow_run_id", "shadow_run_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    shadow_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    real_decision_id: Mapped[int | None] = mapped_column(BigInteger)
    proposal_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    parameter_version_id: Mapped[int | None] = mapped_column(BigInteger)


class ShadowEvaluation(Base, TimestampMixin):
    __tablename__ = "shadow_evaluations"

    __table_args__ = (
        Index("ix_shadow_evaluations_shadow_decision_id", "shadow_decision_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    shadow_decision_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    real_trade_id: Mapped[int | None] = mapped_column(BigInteger)
    shadow_pnl_sim: Mapped[float | None] = mapped_column(Numeric(20, 8))
    real_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8))
    diff: Mapped[float | None] = mapped_column(Numeric(20, 8))
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
