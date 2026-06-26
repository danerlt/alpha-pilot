"""阶段1: format_notification 事件→通知消息映射单测。"""
from __future__ import annotations

from datetime import datetime, timezone

from src.services.events.contracts import EventEnvelope
from src.services.notification.formatter import (
    NotificationMessage,
    format_notification,
    severity_rank,
)


def _envelope(event_type: str, payload: dict, *, trading_mode: str = "testnet") -> EventEnvelope:
    return EventEnvelope(
        event_id=f"evt-{event_type}",
        account_id=1,
        trading_mode=trading_mode,
        occurred_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        trace_id="trace-x",
        schema_version=1,
        event_type=event_type,
        payload=payload,
    )


def test_circuit_breaker_maps_to_critical():
    msg = format_notification(_envelope("circuit_breaker.triggered", {"reason": "daily_loss>3%"}))
    assert isinstance(msg, NotificationMessage)
    assert msg.severity == "critical"
    assert "熔断" in msg.title
    assert "daily_loss>3%" in msg.body
    assert msg.event_id == "evt-circuit_breaker.triggered"


def test_order_failed_maps_to_warn_with_reason():
    msg = format_notification(_envelope("order.failed", {"order_id": 7, "reason": "insufficient balance"}))
    assert msg is not None
    assert msg.severity == "warn"
    assert "insufficient balance" in msg.body


def test_risk_event_uses_payload_severity():
    crit = format_notification(_envelope(
        "risk.event.triggered",
        {"risk_event_id": 3, "event_subtype": "MAX_DRAWDOWN", "severity": "critical", "symbol": "BTCUSDT"},
    ))
    assert crit.severity == "critical"
    warn = format_notification(_envelope(
        "risk.event.triggered",
        {"risk_event_id": 4, "event_subtype": "SLIPPAGE", "severity": "warn", "symbol": "ETHUSDT"},
    ))
    assert warn.severity == "warn"
    assert "ETHUSDT" in warn.body


def test_position_opened_maps_to_info():
    msg = format_notification(_envelope(
        "position.opened",
        {"position_id": 1, "symbol": "BTCUSDT", "quantity": 0.01, "entry_price": 50000.0, "stop_loss": 49000.0},
    ))
    assert msg.severity == "info"
    assert "BTCUSDT" in msg.title or "BTCUSDT" in msg.body


def test_trade_closed_shows_pnl():
    win = format_notification(_envelope(
        "trade.closed",
        {"trade_id": 9, "symbol": "BTCUSDT", "pnl": 123.45, "pnl_pct": 0.02, "exit_reason": "take_profit"},
    ))
    assert win.severity == "info"
    assert "123.45" in win.body


def test_manual_override_maps_to_warn():
    msg = format_notification(_envelope(
        "manual.override",
        {"operator_user_id": 1, "action": "close_all", "target": "account:1", "reason": "emergency"},
    ))
    assert msg.severity == "warn"
    assert "close_all" in msg.body


def test_non_alert_event_returns_none():
    assert format_notification(_envelope("candle.closed", {"symbol": "BTCUSDT"})) is None
    assert format_notification(_envelope("indicators.computed", {})) is None


def test_trading_mode_appears_in_message():
    msg = format_notification(_envelope(
        "circuit_breaker.triggered", {"reason": "x"}, trading_mode="mainnet",
    ))
    assert msg.trading_mode == "mainnet"
    assert "MAINNET" in msg.title or "MAINNET" in msg.body


def test_severity_rank_ordering():
    assert severity_rank("info") < severity_rank("warn") < severity_rank("critical")
