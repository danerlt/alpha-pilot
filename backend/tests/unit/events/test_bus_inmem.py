from __future__ import annotations

from datetime import datetime, timezone

from src.services.events.bus import InMemoryEventBus
from src.services.events.contracts import CandleClosed, EventEnvelope
from src.services.events.ids import new_event_id


def _make_envelope(evt: CandleClosed) -> EventEnvelope:
    return EventEnvelope(
        event_id=new_event_id(),
        account_id=1,
        trading_mode="testnet",
        occurred_at=datetime.now(timezone.utc),
        trace_id="t1",
        schema_version=1,
        event_type=evt.event_type,
        payload=evt.model_dump(mode="json"),
    )


def _candle() -> CandleClosed:
    return CandleClosed(
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1, high=2, low=0.5, close=1.5, volume=100,
    )


def test_inmem_bus_delivers_to_single_subscriber():
    bus = InMemoryEventBus()
    received: list[EventEnvelope] = []
    bus.subscribe("market.*", received.append)

    env = _make_envelope(_candle())
    bus.publish("market.candle", env)

    assert len(received) == 1
    assert received[0].event_type == "candle.closed"


def test_inmem_bus_fan_out_to_multiple_subscribers():
    bus = InMemoryEventBus()
    a: list[EventEnvelope] = []
    b: list[EventEnvelope] = []
    bus.subscribe("market.*", a.append)
    bus.subscribe("market.*", b.append)

    bus.publish("market.candle", _make_envelope(_candle()))
    assert len(a) == 1 and len(b) == 1


def test_inmem_bus_pattern_matches_event_type_too():
    """Subscriber pattern can match envelope.event_type, not only the stream."""
    bus = InMemoryEventBus()
    received: list[EventEnvelope] = []
    bus.subscribe("candle.closed", received.append)

    bus.publish("arbitrary-stream-name", _make_envelope(_candle()))
    assert len(received) == 1


def test_inmem_bus_pattern_miss_does_not_deliver():
    bus = InMemoryEventBus()
    received: list[EventEnvelope] = []
    bus.subscribe("decision.*", received.append)

    bus.publish("market.candle", _make_envelope(_candle()))
    assert received == []


def test_inmem_bus_subscriber_exception_isolates_others():
    """One subscriber raising must not block the others."""
    bus = InMemoryEventBus()

    def bad(env):
        raise RuntimeError("boom")

    good: list[EventEnvelope] = []
    bus.subscribe("market.*", bad)
    bus.subscribe("market.*", good.append)

    bus.publish("market.candle", _make_envelope(_candle()))
    assert len(good) == 1
