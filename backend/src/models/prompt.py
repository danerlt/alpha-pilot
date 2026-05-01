from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"
    __table_args__ = (
        Index("ix_prompt_templates_name_version", "name", "version", unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    system_template: Mapped[str] = mapped_column(Text, nullable=False)
    user_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables_json: Mapped[dict | None] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger)


class ProposalDraft(Base, TimestampMixin):
    __tablename__ = "proposal_drafts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Fresh table — NO Python default; callers must pass account_id explicitly.
    account_id: Mapped[int] = mapped_column(
        nullable=False
    )
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    template_id: Mapped[int | None] = mapped_column(BigInteger)
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    rendered_system: Mapped[str] = mapped_column(Text, nullable=False)
    rendered_user: Mapped[str] = mapped_column(Text, nullable=False)
