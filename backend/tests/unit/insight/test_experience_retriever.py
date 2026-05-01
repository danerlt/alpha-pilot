"""Tests for ExperienceRetriever (V0.1 tag-based)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.insight.experience.retriever import ExperienceRetriever, ExperienceSummary
from src.models import Base, ExperienceV2


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _seed(session, entries: list[dict]):
    """entries: each dict overrides the defaults for one row.

    Defaults: account_id=1, symbol=BTCUSDT, trading_mode=testnet,
    created_at bumped per row so ordering is deterministic.
    """
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i, e in enumerate(entries):
        ev = ExperienceV2(
            account_id=e.get("account_id", 1),
            trading_mode=e.get("trading_mode", "testnet"),
            symbol=e.get("symbol", "BTCUSDT"),
            regime_at_open=e.get("regime_at_open"),
            strategy_mode=e.get("strategy_mode"),
            pnl_pct=e.get("pnl_pct"),
            hold_duration=e.get("hold_duration"),
            exit_reason=e.get("exit_reason"),
            created_at=base_time + timedelta(minutes=i),
            updated_at=base_time + timedelta(minutes=i),
        )
        session.add(ev)
    session.flush()


def test_top_k_returns_most_recent_first(session):
    _seed(session, [
        {"pnl_pct": 0.01, "exit_reason": "take_profit"},
        {"pnl_pct": -0.02, "exit_reason": "stop_loss"},
        {"pnl_pct": 0.03, "exit_reason": "ai_close"},
    ])
    retriever = ExperienceRetriever(session)
    results = retriever.top_k(account_id=1, symbol="BTCUSDT", limit=5)
    assert len(results) == 3
    # Most recent is last-inserted (index 2 → +2 min)
    assert results[0].exit_reason == "ai_close"
    assert results[1].exit_reason == "stop_loss"
    assert results[2].exit_reason == "take_profit"


def test_top_k_respects_limit(session):
    _seed(session, [{"pnl_pct": 0.0} for _ in range(10)])
    retriever = ExperienceRetriever(session)
    results = retriever.top_k(account_id=1, symbol="BTCUSDT", limit=3)
    assert len(results) == 3


def test_top_k_filters_by_symbol(session):
    _seed(session, [
        {"symbol": "BTCUSDT", "exit_reason": "btc1"},
        {"symbol": "ETHUSDT", "exit_reason": "eth1"},
        {"symbol": "BTCUSDT", "exit_reason": "btc2"},
    ])
    retriever = ExperienceRetriever(session)
    btc = retriever.top_k(account_id=1, symbol="BTCUSDT", limit=5)
    eth = retriever.top_k(account_id=1, symbol="ETHUSDT", limit=5)
    assert {r.exit_reason for r in btc} == {"btc1", "btc2"}
    assert {r.exit_reason for r in eth} == {"eth1"}


def test_top_k_filters_by_regime(session):
    _seed(session, [
        {"regime_at_open": "trending_up", "exit_reason": "up1"},
        {"regime_at_open": "ranging", "exit_reason": "rng1"},
        {"regime_at_open": "trending_up", "exit_reason": "up2"},
    ])
    retriever = ExperienceRetriever(session)
    up = retriever.top_k(account_id=1, symbol="BTCUSDT", regime="trending_up", limit=5)
    assert {r.exit_reason for r in up} == {"up1", "up2"}


def test_top_k_filters_by_strategy_mode(session):
    _seed(session, [
        {"strategy_mode": "ai_trend", "exit_reason": "a"},
        {"strategy_mode": "ai_breakout", "exit_reason": "b"},
    ])
    retriever = ExperienceRetriever(session)
    trend = retriever.top_k(account_id=1, symbol="BTCUSDT", strategy_mode="ai_trend", limit=5)
    assert {r.exit_reason for r in trend} == {"a"}


def test_top_k_filters_by_account_id(session):
    _seed(session, [
        {"account_id": 1, "symbol": "BTCUSDT", "exit_reason": "own"},
        {"account_id": 2, "symbol": "ETHUSDT", "exit_reason": "other"},
    ])
    retriever = ExperienceRetriever(session)
    mine = retriever.top_k(account_id=1, symbol="BTCUSDT", limit=5)
    assert all(r.exit_reason == "own" for r in mine)
    assert len(mine) == 1


def test_top_k_returns_empty_when_no_match(session):
    retriever = ExperienceRetriever(session)
    results = retriever.top_k(account_id=999, symbol="DOGEUSDT", limit=5)
    assert results == []


def test_result_type_is_experience_summary(session):
    _seed(session, [{"pnl_pct": 0.05, "hold_duration": 3600, "exit_reason": "ai_close"}])
    retriever = ExperienceRetriever(session)
    results = retriever.top_k(account_id=1, symbol="BTCUSDT", limit=1)
    assert isinstance(results[0], ExperienceSummary)
    assert results[0].pnl_pct == 0.05
    assert results[0].hold_duration == 3600
    assert results[0].exit_reason == "ai_close"
