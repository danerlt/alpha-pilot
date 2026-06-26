"""阶段2: NotificationService 过滤/去重/多 channel 容错单测。"""
from __future__ import annotations

from datetime import datetime, timezone

from src.services.events.contracts import EventEnvelope
from src.services.notification.formatter import NotificationMessage
from src.services.notification.service import NotificationService


class _RecordingChannel:
    def __init__(self, name: str, fail: bool = False):
        self.name = name
        self.fail = fail
        self.sent: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> None:
        if self.fail:
            raise RuntimeError(f"{self.name} boom")
        self.sent.append(message)


def _envelope(event_type: str, payload: dict, *, event_id: str = "evt-1") -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id, account_id=1, trading_mode="testnet",
        occurred_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
        trace_id="t", schema_version=1, event_type=event_type, payload=payload,
    )


def test_dispatch_sends_to_all_channels():
    a, b = _RecordingChannel("a"), _RecordingChannel("b")
    svc = NotificationService(channels=[a, b], min_severity="info")
    sent = svc.dispatch(_envelope("circuit_breaker.triggered", {"reason": "x"}))
    assert sent is True
    assert len(a.sent) == 1 and len(b.sent) == 1


def test_below_min_severity_is_skipped():
    a = _RecordingChannel("a")
    svc = NotificationService(channels=[a], min_severity="critical")
    # position.opened 是 info < critical → 跳过
    sent = svc.dispatch(_envelope("position.opened", {
        "position_id": 1, "symbol": "BTCUSDT", "quantity": 0.1, "entry_price": 1.0, "stop_loss": 0.9,
    }))
    assert sent is False
    assert a.sent == []


def test_non_alert_event_is_skipped():
    a = _RecordingChannel("a")
    svc = NotificationService(channels=[a], min_severity="info")
    assert svc.dispatch(_envelope("candle.closed", {"symbol": "BTCUSDT"})) is False
    assert a.sent == []


def test_duplicate_event_id_dispatched_once():
    a = _RecordingChannel("a")
    svc = NotificationService(channels=[a], min_severity="info")
    env = _envelope("circuit_breaker.triggered", {"reason": "x"}, event_id="dup-1")
    assert svc.dispatch(env) is True
    assert svc.dispatch(env) is False  # 同 event_id 第二次跳过
    assert len(a.sent) == 1


def test_one_channel_failure_does_not_block_others():
    bad, good = _RecordingChannel("bad", fail=True), _RecordingChannel("good")
    svc = NotificationService(channels=[bad, good], min_severity="info")
    sent = svc.dispatch(_envelope("circuit_breaker.triggered", {"reason": "x"}))
    assert sent is True  # 至少一个 channel 成功
    assert len(good.sent) == 1


def test_all_channels_failure_returns_false():
    bad = _RecordingChannel("bad", fail=True)
    svc = NotificationService(channels=[bad], min_severity="info")
    assert svc.dispatch(_envelope("circuit_breaker.triggered", {"reason": "x"})) is False


def test_build_channels_log_only_by_default():
    from types import SimpleNamespace

    from src.services.notification.service import build_channels_from_config

    cfg = SimpleNamespace(
        NOTIFY_TELEGRAM_BOT_TOKEN="", NOTIFY_TELEGRAM_CHAT_ID="",
        NOTIFY_EMAIL_SMTP_HOST="", NOTIFY_EMAIL_TO=[],
    )
    channels = build_channels_from_config(cfg)
    assert [c.name for c in channels] == ["log"]


def test_build_channels_adds_telegram_and_email_when_configured():
    from types import SimpleNamespace

    from src.services.notification.service import build_channels_from_config

    cfg = SimpleNamespace(
        NOTIFY_TELEGRAM_BOT_TOKEN="tok", NOTIFY_TELEGRAM_CHAT_ID="chat",
        NOTIFY_EMAIL_SMTP_HOST="smtp.x", NOTIFY_EMAIL_SMTP_PORT=587,
        NOTIFY_EMAIL_USERNAME="u", NOTIFY_EMAIL_PASSWORD="p",
        NOTIFY_EMAIL_FROM="a@x", NOTIFY_EMAIL_TO=["b@y"], NOTIFY_EMAIL_USE_TLS=True,
    )
    names = [c.name for c in build_channels_from_config(cfg)]
    assert names == ["log", "telegram", "email"]
