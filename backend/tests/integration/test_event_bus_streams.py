"""End-to-end Redis Streams: publish -> consume group -> ack."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from testcontainers.redis import RedisContainer

from src.events.bus import RedisStreamsBus
from src.events.contracts import CandleClosed, EventEnvelope
from src.events.ids import new_event_id


@pytest.fixture(scope="module")
def redis_url():
    with RedisContainer("redis:7-alpine") as rc:
        host = rc.get_container_host_ip()
        port = rc.get_exposed_port(rc.port)
        yield f"redis://{host}:{port}/0"


def _make_envelope(symbol: str) -> EventEnvelope:
    evt = CandleClosed(
        symbol=symbol, timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1, high=2, low=0.5, close=1.5, volume=100,
    )
    return EventEnvelope(
        event_id=new_event_id(), account_id=1, trading_mode="testnet",
        occurred_at=datetime.now(timezone.utc), trace_id="t1",
        schema_version=1, event_type=evt.event_type,
        payload=evt.model_dump(mode="json"),
    )


def test_publish_and_consume_single_message(redis_url):
    bus = RedisStreamsBus(redis_url)
    bus.ensure_group("market.candle.a", "group-a")

    env = _make_envelope("BTCUSDT")
    bus.publish("market.candle.a", env)

    messages = list(bus.consume("market.candle.a", "group-a", "c1", count=1, block_ms=500))
    assert len(messages) == 1
    msg_id, received = messages[0]
    assert received.event_type == "candle.closed"
    assert received.payload["symbol"] == "BTCUSDT"

    bus.ack("market.candle.a", "group-a", msg_id)

    # After ack, a fresh consume on the same group should find nothing new.
    more = list(bus.consume("market.candle.a", "group-a", "c1", count=1, block_ms=100))
    assert more == []


def test_publish_trims_to_maxlen(redis_url):
    bus = RedisStreamsBus(redis_url, default_maxlen=5)
    for i in range(20):
        bus.publish("market.trim.b", _make_envelope(f"SYM{i}"))
    import redis as redis_lib
    r = redis_lib.from_url(redis_url, decode_responses=True)
    length = r.xlen("market.trim.b")
    assert length <= 10, f"expected trim to ~5, got {length}"


def test_dead_letter_writes_to_deadletter_stream(redis_url):
    bus = RedisStreamsBus(redis_url)
    env = _make_envelope("DEAD")
    bus.dead_letter("market.dead.c", env, reason="test")

    import redis as redis_lib
    r = redis_lib.from_url(redis_url, decode_responses=True)
    # Dead-letter stream naming: deadletter.<original_stream>
    length = r.xlen("deadletter.market.dead.c")
    assert length == 1
