from datetime import date
from sqlalchemy import String, Numeric, Date, BigInteger, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, BigIntPk, TimestampMixin
from src.shared.enums import TradingMode


class DailyReport(Base, TimestampMixin):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losing_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    win_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    total_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    total_pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0)
    max_single_loss: Mapped[float | None] = mapped_column(Numeric(20, 8))
    max_drawdown: Mapped[float | None] = mapped_column(Numeric(20, 8))
    risk_events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[dict | None] = mapped_column(JSON)  # 典型案例等补充信息
