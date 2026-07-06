from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class LabCandidate(Base):
    """策略实验室候选 (handoff 3.5): 受控进化流水线 QUEUED→SHADOW→CANARY→LIVE。"""

    __tablename__ = "lab_candidates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    params_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED", index=True)
    shadow_run_id: Mapped[str | None] = mapped_column(String(64), index=True)
    shadow_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shadow_days_target: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    promoted_by: Mapped[int | None] = mapped_column(BigInteger)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rollback_reason: Mapped[str | None] = mapped_column(Text)
