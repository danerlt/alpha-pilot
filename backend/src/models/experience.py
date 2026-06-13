from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.common.enums import TradingMode
from src.models.base import Base


class ExperienceRecord(Base):
    """
    交易经验库（V0.1 基础版）：
    记录已平仓交易的结构化结果，不做 LLM 摘要。
    """
    __tablename__ = "experience_store"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    trade_id: Mapped[int] = mapped_column(nullable=False, unique=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    regime: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    indicator_snapshot: Mapped[dict | None] = mapped_column(JSON)   # 开仓时指标快照
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    exit_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    exit_reason: Mapped[str] = mapped_column(String(30), nullable=False)
    holding_seconds: Mapped[int | None] = mapped_column(BigInteger)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
