from datetime import datetime
from sqlalchemy import String, BigInteger, Numeric, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, BigIntPk, TimestampMixin
from src.shared.enums import TradingMode


class Candle(Base, TimestampMixin):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)  # 15m, 1h
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(30, 8), nullable=False)

    __table_args__ = (
        Index("ix_candles_symbol_timeframe_open_time", "symbol", "timeframe", "open_time", unique=True),
    )
