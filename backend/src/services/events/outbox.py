"""Outbox writer — persists events in the same DB transaction as business writes.

Usage pattern inside a service:

    writer = OutboxWriter()
    with Session() as s:
        pos = Position(...)
        s.add(pos)
        s.flush()
        writer.record(
            s,
            aggregate_type="position",
            aggregate_id=pos.id,
            event=PositionOpened(...),
            account_id=1,
            trading_mode="testnet",
            trace_id=trace_id,
        )
        s.commit()

The EventShuttle worker later reads unpublished rows and forwards them
to Redis Streams, marking `published_at` on success.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models.event_store import EventOutbox
from src.services.events.contracts import EventEnvelope, _Event
from src.services.events.ids import new_event_id


class OutboxWriter:
    """Stateless helper; safe to instantiate per call or as a singleton."""

    def record(
        self,
        session: Session,
        *,
        aggregate_type: str,
        aggregate_id: int | None,
        event: _Event,
        account_id: int = 1,
        trading_mode: str = "testnet",
        trace_id: str,
    ) -> EventOutbox:
        """Attach an event_outbox row to the caller's session (no commit)."""
        event_id = new_event_id()
        envelope = EventEnvelope(
            event_id=event_id,
            account_id=account_id,
            trading_mode=trading_mode,
            occurred_at=datetime.now(timezone.utc),
            trace_id=trace_id,
            schema_version=1,
            event_type=event.event_type,
            payload=event.model_dump(mode="json"),
        )
        row = EventOutbox(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event.event_type,
            event_id=event_id,
            payload_json=envelope.model_dump(mode="json"),
        )
        session.add(row)
        return row
