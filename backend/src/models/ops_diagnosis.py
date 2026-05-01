from __future__ import annotations

from sqlalchemy import BigInteger, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class OpsDiagnosis(Base):
    __tablename__ = "ops_diagnoses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    triggered_by_event_id: Mapped[str | None] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    pattern_matched: Mapped[str | None] = mapped_column(String(100))
    llm_narrative: Mapped[str | None] = mapped_column(Text)
    recommendations_json: Mapped[dict | None] = mapped_column(JSON)
