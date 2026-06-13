from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.common.enums import TradingMode
from src.models.base import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    position_id: Mapped[int] = mapped_column(nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False, default="LONG")
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    exit_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    exit_reason: Mapped[str] = mapped_column(String(30), nullable=False)  # TradeExitReason value
    strategy_mode: Mapped[str | None] = mapped_column(String(30))
    regime: Mapped[str | None] = mapped_column(String(20))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    holding_seconds: Mapped[int | None] = mapped_column(BigInteger)
    ai_decision_id: Mapped[int | None] = mapped_column(BigInteger)
    open_order_id: Mapped[int | None] = mapped_column(BigInteger)
    close_order_id: Mapped[int | None] = mapped_column(BigInteger)
