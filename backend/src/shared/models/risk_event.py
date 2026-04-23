from datetime import datetime
from sqlalchemy import String, DateTime, BigInteger, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, BigIntPk, TimestampMixin
from src.shared.enums import TradingMode


class RiskEvent(Base, TimestampMixin):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # 例如: CIRCUIT_BREAKER_TRIGGERED, STOP_LOSS_HIT, API_ERROR, DAILY_LOSS_LIMIT
    symbol: Mapped[str | None] = mapped_column(String(20))
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    position_id: Mapped[int | None] = mapped_column(BigInteger)
