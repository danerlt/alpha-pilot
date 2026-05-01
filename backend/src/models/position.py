from datetime import datetime
from sqlalchemy import BigInteger, String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base
from src.common.enums import TradingMode, PositionStatus


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=PositionStatus.OPEN.value)
    side: Mapped[str] = mapped_column(String(10), nullable=False, default="LONG")  # V0.1 仅 LONG
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    stop_loss: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    take_profit: Mapped[float | None] = mapped_column(Numeric(20, 8))
    current_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    unrealized_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8))
    unrealized_pnl_pct: Mapped[float | None] = mapped_column(Numeric(10, 6))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_decision_id: Mapped[int | None] = mapped_column(BigInteger)
