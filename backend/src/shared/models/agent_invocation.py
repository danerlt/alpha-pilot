from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, BigIntPk, TimestampMixin


class AgentInvocation(Base, TimestampMixin):
    __tablename__ = "agent_invocations"

    __table_args__ = (
        Index("ix_agent_invocations_occurred_at", "occurred_at"),
        Index("ix_agent_invocations_prompt_template_id", "prompt_template_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    # Fresh table — NO Python default; callers must pass account_id explicitly.
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), nullable=False
    )
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_template_id: Mapped[int | None] = mapped_column(BigInteger)
    llm_provider: Mapped[str | None] = mapped_column(String(30))
    llm_model: Mapped[str | None] = mapped_column(String(60))
    input_json: Mapped[dict | None] = mapped_column(JSON)
    output_json: Mapped[dict | None] = mapped_column(JSON)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    error: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
