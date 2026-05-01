from __future__ import annotations

from src.models import EventInbox, EventOutbox


def test_event_inbox_has_unique_consumer_event_id_index():
    idx_names = {i.name for i in EventInbox.__table__.indexes}
    assert "ix_event_inbox_consumer_name_event_id" in idx_names
    idx = next(
        i for i in EventInbox.__table__.indexes
        if i.name == "ix_event_inbox_consumer_name_event_id"
    )
    assert idx.unique is True


def test_event_outbox_required_fields():
    cols = set(EventOutbox.__table__.columns.keys())
    assert {
        "aggregate_type",
        "aggregate_id",
        "event_type",
        "event_id",
        "payload_json",
        "published_at",
        "failed_attempts",
        "last_error",
    } <= cols


def test_event_outbox_failed_attempts_default_zero():
    col = EventOutbox.__table__.columns["failed_attempts"]
    assert col.default is not None
    assert col.default.arg == 0
