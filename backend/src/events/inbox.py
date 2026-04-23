"""Inbox idempotency guard for event consumers.

Usage:

    guard = InboxGuard(consumer_name="notifier")
    for msg_id, envelope in bus.consume(...):
        with Session() as s:
            if not guard.claim(s, envelope.event_id):
                bus.ack(...)  # already processed, just ack
                continue
            handle(envelope)   # business logic
            s.commit()
        bus.ack(...)

Uses SAVEPOINT (session.begin_nested) so a duplicate-event IntegrityError
only rolls back the inbox INSERT, not the caller's other pending work in
the same outer transaction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.shared.models.event_store import EventInbox


@dataclass
class InboxGuard:
    consumer_name: str

    def claim(self, session: Session, event_id: str) -> bool:
        """Try to record (consumer, event_id). Returns True if first-time, False if duplicate.

        A SAVEPOINT wraps the INSERT; on duplicate IntegrityError only the savepoint
        rolls back, leaving the caller's other pending changes alive.
        """
        row = EventInbox(
            consumer_name=self.consumer_name,
            event_id=event_id,
            processed_at=datetime.now(timezone.utc),
        )
        sp = session.begin_nested()
        session.add(row)
        try:
            session.flush()
            sp.commit()
            return True
        except IntegrityError:
            sp.rollback()
            return False
