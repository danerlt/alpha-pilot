from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class FactorDefinition(Base):
    __tablename__ = "factor_definitions"

    # Declare indexes on the model too (not only in migrations) so:
    #  - Base.metadata.create_all(e.g. SQLite unit tests) produces matching schema
    #  - tests checking model.__table__.indexes see what really exists in prod DB
    __table_args__ = (
        Index("ix_factor_definitions_name_version", "name", "version", unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    inputs_json: Mapped[dict | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    formula_code_ref: Mapped[str | None] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FactorSnapshot(Base):
    __tablename__ = "factor_snapshots"

    __table_args__ = (
        Index(
            "ix_factor_snapshots_unique",
            "account_id", "trading_mode", "symbol", "timeframe", "open_time",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Fresh table — NO Python default; callers must set account_id explicitly
    # (see Task 1 convention).
    account_id: Mapped[int] = mapped_column(
        nullable=False
    )
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    factors_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    factor_def_versions_json: Mapped[dict | None] = mapped_column(JSON)


class FactorCandidate(Base):
    __tablename__ = "factor_candidates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proposed_by_agent: Mapped[str] = mapped_column(String(40), nullable=False, default="factor_ai")
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    formula_code_ref: Mapped[str | None] = mapped_column(String(200))
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    validation_report_json: Mapped[dict | None] = mapped_column(JSON)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
