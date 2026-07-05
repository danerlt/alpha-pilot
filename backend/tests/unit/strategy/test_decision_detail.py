"""DecisionDetailService 单测 — 聚合 decision + review + guard + orders。"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.common.exception.errors import DBException
from src.models import Base
from src.models.decision import AIDecision
from src.models.decision_review import DecisionReview
from src.models.factor import FactorSnapshot
from src.models.order import Order
from src.models.risk_event import RiskEvent
from src.services.strategy.decision_detail import DecisionDetailService


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _seed(session) -> int:
    now = datetime.now(tz=timezone.utc)
    snap = FactorSnapshot(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        open_time=now, factors_json={"trend_strength": 0.8},
    )
    session.add(snap)
    session.flush()
    d = AIDecision(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        decided_at=now, action="OPEN_LONG", confidence=0.72,
        entry_price=50_000, stop_loss=49_000, take_profit=52_000,
        position_size_pct=0.1, strategy_mode="ai_trend",
        reasoning=["EMA stack bullish"], is_fallback=False,
        factor_snapshot_id=snap.id, prompt_input={"context_hash": "h" * 64},
    )
    session.add(d)
    session.flush()
    session.add(DecisionReview(
        decision_id=d.id, reviewer_type="rule", result="approve",
    ))
    session.add(RiskEvent(
        account_id=1, trading_mode="testnet", event_type="GUARD_PASS",
        symbol="BTCUSDT", triggered_at=now, description="all_checks_passed",
        resolved=True, decision_id=d.id,
    ))
    session.add(Order(
        account_id=1, trading_mode="testnet", trace_id="x" * 32,
        symbol="BTCUSDT", side="BUY", order_type="MARKET",
        quantity=0.01, status="FILLED", ai_decision_id=d.id,
        submitted_at=now,
    ))
    session.commit()
    return d.id


def test_get_detail_aggregates_all_sections(session):
    decision_id = _seed(session)
    detail = DecisionDetailService(session).get_detail(
        decision_id, trading_mode="testnet",
    )
    assert detail["id"] == decision_id
    assert detail["action"] == "OPEN_LONG"
    assert detail["features"]["factors"] == {"trend_strength": 0.8}
    assert detail["features"]["prompt_input"]["context_hash"] == "h" * 64
    assert len(detail["reviews"]) == 1
    assert detail["reviews"][0]["result"] == "approve"
    assert len(detail["guard_events"]) == 1
    assert detail["guard_events"][0]["event_type"] == "GUARD_PASS"
    assert len(detail["orders"]) == 1
    assert detail["orders"][0]["side"] == "BUY"


def test_get_detail_not_found_raises(session):
    with pytest.raises(DBException):
        DecisionDetailService(session).get_detail(999999, trading_mode="testnet")


def test_get_detail_wrong_trading_mode_raises(session):
    decision_id = _seed(session)
    with pytest.raises(DBException):
        DecisionDetailService(session).get_detail(decision_id, trading_mode="mainnet")
