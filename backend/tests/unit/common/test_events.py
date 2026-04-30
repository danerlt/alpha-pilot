from datetime import datetime

from src.common.events import BaseEvent


def test_base_event_default_fields():
    e = BaseEvent()
    assert e.user_id is None
    assert e.request_id is None
    assert isinstance(e.occurred_at, datetime)


def test_base_event_with_user():
    e = BaseEvent(user_id=42)
    assert e.user_id == 42
