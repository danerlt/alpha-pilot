from __future__ import annotations

import time
import uuid

from src.events.ids import new_event_id, parse_event_id


def test_new_event_id_is_uuid_v7_shape():
    eid = new_event_id()
    parsed = uuid.UUID(eid)
    assert parsed.version == 7


def test_event_ids_are_time_ordered():
    """UUIDv7 has a 48-bit timestamp prefix, so later IDs sort greater."""
    first = new_event_id()
    time.sleep(0.002)  # advance past the 1ms tick
    second = new_event_id()
    assert first < second, "UUIDv7 ids must be lexicographically time-ordered"


def test_parse_event_id_roundtrip():
    eid = new_event_id()
    parsed = parse_event_id(eid)
    assert str(parsed) == eid


def test_parse_event_id_rejects_non_v7():
    v4 = str(uuid.uuid4())
    import pytest
    with pytest.raises(ValueError):
        parse_event_id(v4)


def test_parse_event_id_rejects_malformed():
    import pytest
    with pytest.raises(ValueError):
        parse_event_id("not-a-uuid")
