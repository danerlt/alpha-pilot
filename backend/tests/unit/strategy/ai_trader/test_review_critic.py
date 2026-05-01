"""Tests for ReviewCritic (rule-based V0.1)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.insight.experience.retriever import ExperienceSummary
from src.models import AIDecision, Base, DecisionReview
from src.strategy.ai_trader.review_critic import ReviewCritic
from src.strategy.proposal import DecisionProposal


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        # Seed a referenced ai_decisions row so decision_id FK is satisfied.
        from datetime import datetime, timezone
        d = AIDecision(
            account_id=1, trading_mode="testnet",
            symbol="BTCUSDT", timeframe="1h",
            decided_at=datetime.now(timezone.utc),
            action="OPEN_LONG",
        )
        s.add(d)
        s.flush()
        yield s, d.id


def _open_long(
    entry=50000.0, sl=49750.0, tp=50500.0,
    strategy_mode="ai_trend",
) -> DecisionProposal:
    """Sensible baseline: 250 SL distance, 500 TP distance → R/R = 2."""
    return DecisionProposal(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        action="OPEN_LONG", confidence=0.7,
        entry_type="MARKET", entry_price=entry,
        stop_loss=sl, take_profit=tp,
        position_size_pct=0.1,
        strategy_mode=strategy_mode, source="ai_trader",
    )


def test_hold_is_auto_approved(session):
    s, did = session
    p = DecisionProposal(
        account_id=1, symbol="X", timeframe="1h",
        action="HOLD", confidence=0.0,
        strategy_mode="ai_observation", source="ai_trader",
    )
    r = ReviewCritic(s).review(
        proposal=p, decision_id=did, regime="ranging", atr=100.0, recent_experience=[],
    )
    assert r.result == "approve"


def test_open_long_in_trending_down_rejected(session):
    s, did = session
    r = ReviewCritic(s).review(
        proposal=_open_long(), decision_id=did,
        regime="trending_down", atr=100.0, recent_experience=[],
    )
    assert r.result == "reject"
    assert "regime_fit" in r.notes


def test_sl_too_tight_rejected(session):
    s, did = session
    # SL distance = 50, ATR=500, min_mult=0.5 → min_distance=250 → reject
    r = ReviewCritic(s).review(
        proposal=_open_long(entry=50000, sl=49950, tp=50500),
        decision_id=did, regime="trending_up", atr=500.0, recent_experience=[],
    )
    assert r.result == "reject"
    assert "sl_distance" in r.notes


def test_sl_too_wide_rejected(session):
    s, did = session
    # SL distance = 3000, ATR=500, max_mult=5 → max_distance=2500 → reject
    r = ReviewCritic(s).review(
        proposal=_open_long(entry=50000, sl=47000, tp=53000),
        decision_id=did, regime="trending_up", atr=500.0, recent_experience=[],
    )
    assert r.result == "reject"


def test_rr_below_threshold_adjusts_tp(session):
    s, did = session
    # SL dist=250, TP dist=200 → R/R=0.8 < 1.5 → adjust TP to 50000 + 250*1.5 = 50375
    r = ReviewCritic(s).review(
        proposal=_open_long(entry=50000, sl=49750, tp=50200),
        decision_id=did, regime="trending_up", atr=200.0, recent_experience=[],
    )
    assert r.result == "adjust"
    assert r.adjustments is not None
    assert abs(r.adjustments["take_profit"] - 50375.0) < 0.01


def test_missing_tp_on_open_long_rejected(session):
    s, did = session
    p = _open_long(entry=50000, sl=49750, tp=None)
    r = ReviewCritic(s).review(
        proposal=p, decision_id=did,
        regime="trending_up", atr=200.0, recent_experience=[],
    )
    assert r.result == "reject"
    assert "missing_take_profit" in r.notes


def test_all_clear_approves(session):
    s, did = session
    r = ReviewCritic(s).review(
        proposal=_open_long(),  # R/R = 2, SL distance = 250
        decision_id=did, regime="trending_up",
        atr=200.0,  # min=100, max=1000 → 250 is OK
        recent_experience=[],
    )
    assert r.result == "approve"


def test_experience_alarm_approves_with_soft_note(session):
    """V0.1: 3 negative recent same-mode trades is informational, not blocking."""
    s, did = session
    recent = [
        ExperienceSummary(symbol="BTCUSDT", regime_at_open="trending_up",
                          strategy_mode="ai_trend", pnl_pct=-0.01,
                          hold_duration=3600, exit_reason="stop_loss"),
        ExperienceSummary(symbol="BTCUSDT", regime_at_open="trending_up",
                          strategy_mode="ai_trend", pnl_pct=-0.005,
                          hold_duration=1800, exit_reason="stop_loss"),
        ExperienceSummary(symbol="BTCUSDT", regime_at_open="trending_up",
                          strategy_mode="ai_trend", pnl_pct=-0.02,
                          hold_duration=2400, exit_reason="stop_loss"),
    ]
    r = ReviewCritic(s).review(
        proposal=_open_long(), decision_id=did,
        regime="trending_up", atr=200.0, recent_experience=recent,
    )
    assert r.result == "approve"
    assert "experience_alarm" in r.notes


def test_review_persists_decision_review_row(session):
    s, did = session
    ReviewCritic(s).review(
        proposal=_open_long(), decision_id=did,
        regime="trending_up", atr=200.0, recent_experience=[],
    )
    rows = s.execute(select(DecisionReview)).scalars().all()
    assert len(rows) == 1
    assert rows[0].reviewer_type == "rule"
    assert rows[0].decision_id == did
