"""Re-export from src.models.event_store (兼容 wrapper, 阶段 3 删)."""
from src.models.event_store import EventInbox, EventOutbox
__all__ = ['EventInbox', 'EventOutbox']
