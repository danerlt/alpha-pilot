from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger, Integer, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode


class AIDecision(Base, TimestampMixin):
    __tablename__ = "ai_decisions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # Action value
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    entry_type: Mapped[str | None] = mapped_column(String(10))
    entry_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    stop_loss: Mapped[float | None] = mapped_column(Numeric(20, 8))
    take_profit: Mapped[float | None] = mapped_column(Numeric(20, 8))
    position_size_pct: Mapped[float | None] = mapped_column(Numeric(5, 4))
    strategy_mode: Mapped[str | None] = mapped_column(String(30))
    reasoning: Mapped[list | None] = mapped_column(JSON)
    risk_note: Mapped[str | None] = mapped_column(Text)
    prompt_input: Mapped[dict | None] = mapped_column(JSON)   # 完整 prompt 输入（审计用）
    raw_output: Mapped[str | None] = mapped_column(Text)      # LLM 原始输出（审计用）
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 是否触发兜底 HOLD
    proposal_draft_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("proposal_drafts.id")
    )
    llm_provider: Mapped[str | None] = mapped_column(String(30))
    llm_model: Mapped[str | None] = mapped_column(String(60))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="ai_trader")
    factor_snapshot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("factor_snapshots.id")
    )
