from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AgentPendingAction(Base):
    """Pilot Agent 提议的写操作 (handoff 3.4): 人工 confirm 前不生效。"""

    __tablename__ = "agent_pending_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invocation_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False, default="config_change")
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    proposed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_by: Mapped[int | None] = mapped_column(BigInteger)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
