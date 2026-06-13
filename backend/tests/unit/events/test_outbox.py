from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.models import Base, EventOutbox
from src.services.events.contracts import CandleClosed
from src.services.events.outbox import OutboxWriter


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _sample_event() -> CandleClosed:
    return CandleClosed(
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1, high=2, low=0.5, close=1.5, volume=100,
    )


def test_record_writes_unpublished_row(session):
    writer = OutboxWriter()
    writer.record(
        session,
        aggregate_type="candle",
        aggregate_id=None,
        event=_sample_event(),
        account_id=1,
        trading_mode="testnet",
        trace_id="t1",
    )
    session.commit()

    rows = session.query(EventOutbox).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.event_type == "candle.closed"
    assert row.published_at is None
    assert row.failed_attempts == 0
    # payload_json is the full EventEnvelope dict
    assert row.payload_json["payload"]["symbol"] == "BTCUSDT"
    assert row.payload_json["account_id"] == 1
    assert row.payload_json["trace_id"] == "t1"
    # event_id on the row matches the envelope's event_id
    assert row.event_id == row.payload_json["event_id"]


def test_record_does_not_commit_caller_session(session):
    """The writer adds to the session but doesn't flush/commit on its own."""
    writer = OutboxWriter()
    writer.record(
        session,
        aggregate_type="candle", aggregate_id=None,
        event=_sample_event(),
        account_id=1, trading_mode="testnet", trace_id="t2",
    )
    # Before commit, other connections shouldn't see the row.
    # Simplest check: row is in session.new
    new_objs = list(session.new)
    assert any(isinstance(o, EventOutbox) for o in new_objs)


def test_record_generates_uuidv7_event_id(session):
    import uuid
    writer = OutboxWriter()
    writer.record(
        session,
        aggregate_type="candle", aggregate_id=None,
        event=_sample_event(),
        account_id=1, trading_mode="testnet", trace_id="t3",
    )
    session.commit()

    row = session.query(EventOutbox).first()
    parsed = uuid.UUID(row.event_id)
    assert parsed.version == 7
