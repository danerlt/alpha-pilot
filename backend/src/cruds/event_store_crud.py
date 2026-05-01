"""CRUD for src.models.event_store."""
from __future__ import annotations

from src.models.event_store import EventInbox, EventOutbox
from src.cruds.base_crud import BaseCrud


class EventInboxCrud(BaseCrud[EventInbox]):
    model = EventInbox

event_inbox_crud = EventInboxCrud()

class EventOutboxCrud(BaseCrud[EventOutbox]):
    model = EventOutbox

event_outbox_crud = EventOutboxCrud()
