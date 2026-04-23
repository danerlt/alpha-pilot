"""UUIDv7 event id wrappers.

Event IDs are UUIDv7 so they sort naturally in time order across Redis
Streams, DB indexes, and logs. Centralized here so the underlying library
(currently `uuid6`) can be swapped without touching callers.
"""
from __future__ import annotations

import uuid

import uuid6


def new_event_id() -> str:
    """Generate a new UUIDv7 as the canonical hex-with-dashes string form."""
    return str(uuid6.uuid7())


def parse_event_id(value: str) -> uuid.UUID:
    """Parse an event id string. Raises ValueError if malformed or not UUIDv7."""
    parsed = uuid.UUID(value)
    if parsed.version != 7:
        raise ValueError(f"expected UUIDv7, got v{parsed.version}")
    return parsed
