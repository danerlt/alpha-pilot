"""阶段3: NotificationDispatcher 消费→dispatch→ack 单测 (fake bus 注入)。"""
from __future__ import annotations

from datetime import datetime, timezone

from src.services.events.contracts import EventEnvelope
from src.services.notification.dispatcher import NOTIFIER_GROUP, NotificationDispatcher
from src.services.notification.service import NotificationService


class _RecordingChannel:
    def __init__(self):
        self.name = "rec"
        self.sent = []

    def send(self, message):
        self.sent.append(message)


class _FakeBus:
    def __init__(self, items):
        self._items = items  # list[(stream, msg_id, envelope)]
        self.groups: list[tuple[str, str]] = []
        self.acked: list[tuple[str, str, str]] = []

    def ensure_group(self, stream, group):
        self.groups.append((stream, group))

    def consume_multi(self, streams, group, consumer, *, count=10, block_ms=2000):
        for it in self._items:
            yield it
        self._items = []  # 第二次 run_once 返回空

    def ack(self, stream, group, message_id):
        self.acked.append((stream, group, message_id))
        return 1


def _env(event_type: str, payload: dict, *, event_id: str) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id, account_id=1, trading_mode="testnet",
        occurred_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
        trace_id="t", schema_version=1, event_type=event_type, payload=payload,
    )


def test_setup_creates_group_for_each_stream():
    bus = _FakeBus([])
    svc = NotificationService(channels=[_RecordingChannel()], min_severity="info")
    disp = NotificationDispatcher(bus, svc, streams=["circuit_breaker.triggered", "order.failed"])
    disp.setup()
    assert (("circuit_breaker.triggered", NOTIFIER_GROUP) in bus.groups)
    assert (("order.failed", NOTIFIER_GROUP) in bus.groups)


def test_run_once_dispatches_and_acks():
    ch = _RecordingChannel()
    svc = NotificationService(channels=[ch], min_severity="info")
    env = _env("circuit_breaker.triggered", {"reason": "daily_loss"}, event_id="m1")
    bus = _FakeBus([("circuit_breaker.triggered", "1-0", env)])
    disp = NotificationDispatcher(bus, svc)

    handled = disp.run_once()
    assert handled == 1
    assert len(ch.sent) == 1
    assert bus.acked == [("circuit_breaker.triggered", NOTIFIER_GROUP, "1-0")]


def test_run_once_acks_even_when_below_severity():
    """info 事件低于 warn 阈值不推, 但仍要 ack (否则 stream 卡住)。"""
    ch = _RecordingChannel()
    svc = NotificationService(channels=[ch], min_severity="critical")
    env = _env("position.opened", {
        "position_id": 1, "symbol": "BTCUSDT", "quantity": 0.1, "entry_price": 1.0, "stop_loss": 0.9,
    }, event_id="m2")
    bus = _FakeBus([("position.opened", "2-0", env)])
    disp = NotificationDispatcher(bus, svc)

    disp.run_once()
    assert ch.sent == []  # 未推
    assert bus.acked == [("position.opened", NOTIFIER_GROUP, "2-0")]  # 但已 ack


def test_default_streams_match_alert_event_types():
    from src.services.notification.formatter import ALERT_EVENT_TYPES

    bus = _FakeBus([])
    svc = NotificationService(channels=[_RecordingChannel()], min_severity="info")
    disp = NotificationDispatcher(bus, svc)
    assert set(disp._streams) == set(ALERT_EVENT_TYPES)
