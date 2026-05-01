from datetime import datetime
from sqlalchemy import BigInteger, String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base
from src.common.enums import TradingMode


class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_balance_usdt: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    available_balance_usdt: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    daily_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    daily_pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0)
