"""EventShuttle — moves unpublished event_outbox rows to Redis Streams.

stream_for_event(event_type) maps "candle.closed" -> "candle.closed" by default;
override to route all trade.* to the same stream, etc.

Failure handling:
  - Each publish error increments failed_attempts and records last_error.
  - After MAX_FAILED_ATTEMPTS, the envelope is pushed to the dead-letter
    stream (via bus.dead_letter) and the row is marked published_at to
    prevent infinite re-processing.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Callable, Protocol

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.events.contracts import EventEnvelope
from src.shared.models.event_store import EventOutbox

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 3


class _BusLike(Protocol):
    def publish(self, stream: str, envelope: EventEnvelope, **kw) -> str | None: ...
    def dead_letter(self, stream: str, envelope: EventEnvelope, reason: str) -> None: ...


class EventShuttle:
    def __init__(
        self,
        engine: Engine,
        bus: _BusLike,
        stream_for_event: Callable[[str], str] = lambda t: t,
    ):
        self._engine = engine
        self._bus = bus
        self._stream_for_event = stream_for_event

    def drain_once(self, batch_size: int = 100) -> int:
        """Publish up to batch_size unpublished rows. Returns count successfully published."""
        published = 0
        with Session(self._engine) as s:
            rows = (
                s.execute(
                    select(EventOutbox)
                    .where(EventOutbox.published_at.is_(None))
                    .order_by(EventOutbox.id.asc())
                    .limit(batch_size)
                )
                .scalars()
                .all()
            )
            for row in rows:
                try:
                    envelope = EventEnvelope.model_validate(row.payload_json)
                    stream = self._stream_for_event(row.event_type)
                    self._bus.publish(stream, envelope)
                    row.published_at = datetime.now(timezone.utc)
                    published += 1
                except Exception as e:  # noqa: BLE001 — broad on purpose
                    row.failed_attempts += 1
                    row.last_error = str(e)[:500]
                    logger.exception("shuttle failed for outbox row id=%s", row.id)
                    if row.failed_attempts >= MAX_FAILED_ATTEMPTS:
                        try:
                            envelope = EventEnvelope.model_validate(row.payload_json)
                            self._bus.dead_letter(
                                self._stream_for_event(row.event_type),
                                envelope,
                                reason=row.last_error or "unknown",
                            )
                            row.published_at = datetime.now(timezone.utc)
                        except Exception:
                            logger.exception("dead-letter publish also failed")
            s.commit()
        return published

    def run_forever(self, *, poll_interval_seconds: float = 1.0) -> None:
        while True:
            try:
                self.drain_once()
            except Exception:
                logger.exception("shuttle drain loop error")
            time.sleep(poll_interval_seconds)
