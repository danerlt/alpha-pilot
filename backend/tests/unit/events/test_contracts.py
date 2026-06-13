from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.services.events.contracts import (
    EVENT_TYPE_REGISTRY,
    CandleClosed,
    DecisionProposed,
    EventEnvelope,
    TradeClosed,
)
from src.services.events.ids import new_event_id


def test_envelope_required_fields():
    env = EventEnvelope(
        event_id=new_event_id(),
        account_id=1,
        trading_mode="testnet",
        occurred_at=datetime.now(timezone.utc),
        trace_id="abc",
        schema_version=1,
        event_type="candle.closed",
        payload={},
    )
    assert env.schema_version == 1
    assert env.account_id == 1


def test_envelope_defaults_match_spec():
    """account_id defaults to 1 (single-tenant V0.1) and trading_mode to testnet."""
    env = EventEnvelope(
        event_id=new_event_id(),
        occurred_at=datetime.now(timezone.utc),
        trace_id="t",
        event_type="candle.closed",
        payload={},
    )
    assert env.account_id == 1
    assert env.trading_mode == "testnet"
    assert env.schema_version == 1


def test_candle_closed_payload_serializes():
    evt = CandleClosed(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1.0, high=1.1, low=0.9, close=1.05, volume=100.0,
    )
    data = evt.model_dump(mode="json")
    assert data["symbol"] == "BTCUSDT"
    assert data["volume"] == 100.0


def test_decision_proposed_required_fields():
    evt = DecisionProposed(
        decision_id=42, symbol="BTCUSDT", timeframe="1h",
        action="OPEN_LONG", confidence=0.7,
        source="ai_trader", strategy_mode="ai_trend",
        is_fallback=False,
    )
    assert evt.action == "OPEN_LONG"
    assert evt.source == "ai_trader"


def test_decision_proposed_rejects_invalid_action():
    with pytest.raises(Exception):  # Pydantic ValidationError
        DecisionProposed(
            decision_id=1, symbol="X", timeframe="1h",
            action="OPEN_SHORT",  # V0.1 不支持做空
            confidence=0.5, source="ai_trader",
        )


def test_registry_covers_star_events():
    """V0.1 ★ events must all be in the registry with correct class binding."""
    required = [
        "candle.closed",
        "indicators.computed",
        "regime.classified",
        "decision.proposed",
        "decision.reviewed",
        "decision.rejected",
        "order.submitted",
        "order.filled",
        "order.failed",
        "position.opened",
        "position.updated",
        "position.closed",
        "trade.closed",
        "risk.event.triggered",
        "circuit_breaker.triggered",
    ]
    for event_type in required:
        assert event_type in EVENT_TYPE_REGISTRY, f"{event_type} missing from registry"

    assert EVENT_TYPE_REGISTRY["candle.closed"] is CandleClosed
    assert EVENT_TYPE_REGISTRY["decision.proposed"] is DecisionProposed
    assert EVENT_TYPE_REGISTRY["trade.closed"] is TradeClosed


def test_registry_values_subclass_event_base():
    from src.services.events.contracts import _Event
    for cls in EVENT_TYPE_REGISTRY.values():
        assert issubclass(cls, _Event), f"{cls.__name__} must subclass _Event"


def test_registry_event_type_matches_key():
    """dict key should equal class's event_type ClassVar."""
    for key, cls in EVENT_TYPE_REGISTRY.items():
        assert cls.event_type == key, (
            f"registry key {key!r} doesn't match {cls.__name__}.event_type = {cls.event_type!r}"
        )
