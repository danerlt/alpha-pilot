from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, BigIntPk, TimestampMixin


class DecisionReview(Base, TimestampMixin):
    __tablename__ = "decision_reviews"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ai_decisions.id"), nullable=False)
    reviewer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    adjustments_json: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
