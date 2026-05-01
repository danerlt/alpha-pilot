"""Event bus abstraction with two backends.

InMemoryEventBus -- synchronous fan-out for the Pipeline fast path and unit tests.
RedisStreamsBus  -- persistent, consumer-group-aware Redis Streams backend for
                    inter-plane async delivery and durable side effects.

Conventions:
  - One stream per event family (e.g. "market.candle", "decision.proposed").
  - Consumer groups named after the downstream service (e.g. "notifier").
  - Subscriber patterns use fnmatch-style glob (e.g. "market.*").
"""
from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from typing import Callable, Iterator, Protocol

import redis as redis_lib

from src.services.events.contracts import EventEnvelope

logger = logging.getLogger(__name__)


Handler = Callable[[EventEnvelope], None]


class EventBus(Protocol):
    """Minimal bus surface any implementation provides."""

    def publish(self, stream: str, envelope: EventEnvelope) -> None: ...


# ---------------------------------------------------------------------------
# In-memory bus (Pipeline fast path + unit tests)
# ---------------------------------------------------------------------------

@dataclass
class InMemoryEventBus:
    """Synchronous pub/sub; subscribers matched by fnmatch against stream OR event_type."""

    _subscribers: list[tuple[str, Handler]] = field(default_factory=list)

    def subscribe(self, pattern: str, handler: Handler) -> None:
        self._subscribers.append((pattern, handler))

    def publish(self, stream: str, envelope: EventEnvelope) -> None:
        for pattern, handler in self._subscribers:
            if fnmatch.fnmatch(stream, pattern) or fnmatch.fnmatch(envelope.event_type, pattern):
                try:
                    handler(envelope)
                except Exception:
                    logger.exception("in-mem handler failed for %s", envelope.event_type)


# ---------------------------------------------------------------------------
# Redis Streams bus
# ---------------------------------------------------------------------------

class RedisStreamsBus:
    """Durable, consumer-group-aware bus backed by Redis Streams."""

    def __init__(self, url: str, default_maxlen: int | None = 10_000):
        self._r = redis_lib.from_url(url, decode_responses=True)
        self._default_maxlen = default_maxlen

    def publish(
        self,
        stream: str,
        envelope: EventEnvelope,
        *,
        maxlen: int | None = None,
    ) -> str:
        """Append an envelope to a stream; returns Redis-assigned message id."""
        effective = maxlen if maxlen is not None else self._default_maxlen
        fields = {"envelope": envelope.model_dump_json()}
        if effective is not None:
            return self._r.xadd(stream, fields, maxlen=effective, approximate=True)
        return self._r.xadd(stream, fields)

    def ensure_group(self, stream: str, group: str) -> None:
        """Idempotently create a consumer group; creates the stream if absent."""
        try:
            self._r.xgroup_create(stream, group, id="$", mkstream=True)
        except redis_lib.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def consume(
        self,
        stream: str,
        group: str,
        consumer: str,
        *,
        count: int = 10,
        block_ms: int = 5000,
    ) -> Iterator[tuple[str, EventEnvelope]]:
        """Yield (message_id, envelope) pairs; caller must ack after processing."""
        streams = {stream: ">"}
        response = self._r.xreadgroup(group, consumer, streams, count=count, block=block_ms)
        if not response:
            return
        for _, messages in response:
            for msg_id, fields in messages:
                raw = fields.get("envelope")
                if raw is None:
                    logger.warning("stream %s msg %s has no envelope field", stream, msg_id)
                    continue
                try:
                    env = EventEnvelope.model_validate_json(raw)
                except Exception:
                    logger.exception("failed to parse envelope on %s %s", stream, msg_id)
                    continue
                yield msg_id, env

    def ack(self, stream: str, group: str, message_id: str) -> int:
        return self._r.xack(stream, group, message_id)

    def dead_letter(self, stream: str, envelope: EventEnvelope, reason: str) -> None:
        """Publish a failed envelope to `deadletter.<original_stream>` for triage."""
        dl_stream = f"deadletter.{stream}"
        dl_fields = {
            "envelope": envelope.model_dump_json(),
            "original_stream": stream,
            "reason": reason,
        }
        self._r.xadd(dl_stream, dl_fields, maxlen=1_000, approximate=True)
