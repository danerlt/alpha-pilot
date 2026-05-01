from datetime import datetime
from sqlalchemy import BigInteger, String, Numeric, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base
from src.shared.enums import TradingMode


class RegimeSnapshot(Base):
    __tablename__ = "regime_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    regime: Mapped[str] = mapped_column(String(20), nullable=False)  # RegimeType value
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    features: Mapped[dict | None] = mapped_column(JSON)  # 识别所用特征值
