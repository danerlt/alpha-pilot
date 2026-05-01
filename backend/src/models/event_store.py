from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class EventInbox(Base, TimestampMixin):
    __tablename__ = "event_inbox"

    __table_args__ = (
        Index(
            "ix_event_inbox_consumer_name_event_id",
            "consumer_name", "event_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    consumer_name: Mapped[str] = mapped_column(String(80), nullable=False)
    event_id: Mapped[str] = mapped_column(String(40), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EventOutbox(Base, TimestampMixin):
    __tablename__ = "event_outbox"

    # event_id 索引: catchup / WebSocket _replay_since 都跑
    # `WHERE event_id > since ORDER BY id ASC LIMIT N` (post-Plan5 codereview Risk #6)
    __table_args__ = (
        Index("ix_event_outbox_event_id", "event_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    aggregate_type: Mapped[str] = mapped_column(String(40), nullable=False)
    aggregate_id: Mapped[int | None] = mapped_column(BigInteger)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_id: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
