from __future__ import annotations
import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.events.inbox import InboxGuard
from src.models import Base, EventInbox


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_first_claim_returns_true_and_writes_row(session):
    guard = InboxGuard(consumer_name="notifier")
    assert guard.claim(session, "evt-1") is True
    session.commit()

    rows = session.execute(select(EventInbox)).scalars().all()
    assert len(rows) == 1
    assert rows[0].consumer_name == "notifier"
    assert rows[0].event_id == "evt-1"


def test_second_claim_same_event_returns_false(session):
    guard = InboxGuard(consumer_name="notifier")
    assert guard.claim(session, "evt-1") is True
    session.commit()
    assert guard.claim(session, "evt-1") is False


def test_different_consumers_can_claim_same_event(session):
    a = InboxGuard(consumer_name="a")
    b = InboxGuard(consumer_name="b")
    assert a.claim(session, "evt-x") is True
    session.commit()
    assert b.claim(session, "evt-x") is True
    session.commit()

    rows = session.execute(select(EventInbox)).scalars().all()
    assert len(rows) == 2


def test_duplicate_claim_does_not_abort_caller_session(session):
    """When claim returns False it must use a SAVEPOINT so the caller's
    other pending changes stay alive."""
    from src.models.event_store import EventInbox as EI

    # Pre-claim once.
    guard = InboxGuard(consumer_name="c")
    guard.claim(session, "e1")
    session.commit()

    # Now add some unrelated work, then hit a duplicate claim.
    extra = EI(consumer_name="scratch", event_id="scratch-1", processed_at=__import__("datetime").datetime.now())
    session.add(extra)
    # Duplicate — should NOT rollback the scratch row.
    assert guard.claim(session, "e1") is False
    session.commit()

    names = [r.consumer_name for r in session.execute(select(EI)).scalars().all()]
    assert "scratch" in names, "duplicate claim aborted caller's other pending work"
