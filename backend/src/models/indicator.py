from datetime import datetime
from sqlalchemy import BigInteger, String, Numeric, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base
from src.shared.enums import TradingMode


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ema20: Mapped[float | None] = mapped_column(Numeric(20, 8))
    ema50: Mapped[float | None] = mapped_column(Numeric(20, 8))
    ema200: Mapped[float | None] = mapped_column(Numeric(20, 8))
    rsi: Mapped[float | None] = mapped_column(Numeric(10, 4))
    macd: Mapped[float | None] = mapped_column(Numeric(20, 8))
    macd_signal: Mapped[float | None] = mapped_column(Numeric(20, 8))
    macd_hist: Mapped[float | None] = mapped_column(Numeric(20, 8))
    atr: Mapped[float | None] = mapped_column(Numeric(20, 8))
    bb_upper: Mapped[float | None] = mapped_column(Numeric(20, 8))
    bb_middle: Mapped[float | None] = mapped_column(Numeric(20, 8))
    bb_lower: Mapped[float | None] = mapped_column(Numeric(20, 8))
    volume_ma: Mapped[float | None] = mapped_column(Numeric(30, 8))
    volatility: Mapped[float | None] = mapped_column(Numeric(10, 6))
    extra: Mapped[dict | None] = mapped_column(JSON)  # 额外指标扩展
