"""Multi-tenant entities: Account, RiskProfile, ParameterVersion.

Named account_entity.py (not account.py) to avoid clashing with the existing
AccountSnapshot model in account.py.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, BigIntPk, TimestampMixin


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, default="binance")
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    api_key_encrypted: Mapped[str | None] = mapped_column(Text)
    api_secret_encrypted: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    risk_profile_id: Mapped[int | None] = mapped_column(BigInteger)


class RiskProfile(Base, TimestampMixin):
    __tablename__ = "risk_profiles"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    # No Python-level default — callers must set account_id explicitly on
    # fresh rows so "forgot to pass account_id" surfaces as a programming
    # error rather than silently defaulting to 1.
    account_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    max_position_size_pct: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.20)
    max_daily_loss_pct: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.03)
    max_consecutive_losses: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_single_risk_pct: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.01)
    min_rr_ratio: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.5)
    sl_atr_min_mult: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.5)
    sl_atr_max_mult: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=5.0)
    regime_thresholds_json: Mapped[dict | None] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ParameterVersion(Base, TimestampMixin):
    __tablename__ = "parameter_versions"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    # No Python-level default — see RiskProfile comment above.
    account_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    profile_id: Mapped[int | None] = mapped_column(BigInteger)
    change_type: Mapped[str] = mapped_column(String(40), nullable=False)
    old_value_json: Mapped[dict | None] = mapped_column(JSON)
    new_value_json: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    proposed_by_agent: Mapped[str | None] = mapped_column(String(40))
    validated_by: Mapped[str | None] = mapped_column(String(40))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
