"""Tests for RegimeClassifier — factor-based market regime detection."""
from __future__ import annotations

import os

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.insight.regime.classifier import RegimeClassifier
from src.models import Base, RegimeSnapshot


# ---------------------------------------------------------------------------
# Pure classify() tests — no DB
# ---------------------------------------------------------------------------

def _factors(**overrides) -> dict[str, float]:
    """Build a factors dict with sensible neutrals + overrides."""
    base = {
        "trend_strength": 0.0,
        "momentum_quality": 0.0,
        "volume_confirmation": 0.5,
        "volatility_regime": 0.3,
        "breakout_validity": 0.0,
        "pullback_opportunity": 0.0,
    }
    base.update(overrides)
    return base


def test_classify_trending_up_on_strong_bull_factors():
    clf = RegimeClassifier()
    r = clf.classify(_factors(trend_strength=0.85, volatility_regime=0.3))
    assert r.regime == "trending_up"
    assert 0.3 <= r.confidence <= 1.0


def test_classify_trending_down_on_strong_bear_factors():
    clf = RegimeClassifier()
    r = clf.classify(_factors(trend_strength=-0.85, volatility_regime=0.3))
    assert r.regime == "trending_down"
    assert r.confidence >= 0.3


def test_classify_ranging_on_flat_low_vol():
    clf = RegimeClassifier()
    r = clf.classify(_factors(trend_strength=0.1, volatility_regime=0.2))
    assert r.regime == "ranging"
    assert r.confidence >= 0.3


def test_classify_chaotic_on_high_volatility():
    clf = RegimeClassifier()
    r = clf.classify(_factors(trend_strength=0.7, volatility_regime=0.9))
    assert r.regime == "chaotic"


def test_classify_chaotic_on_broken_breakout():
    clf = RegimeClassifier()
    r = clf.classify(_factors(breakout_validity=-0.8, volatility_regime=0.3))
    assert r.regime == "chaotic"


def test_classify_fallback_to_ranging_when_ambiguous():
    """Mid-band trend with moderate vol → low-confidence ranging."""
    clf = RegimeClassifier()
    r = clf.classify(_factors(trend_strength=0.45, volatility_regime=0.5))
    assert r.regime == "ranging"
    assert r.confidence == 0.3  # explicit fallback confidence


def test_custom_thresholds_override_defaults():
    clf = RegimeClassifier(thresholds={"trending_strength": 0.4})
    # trend 0.5 > 0.4 threshold → trending_up
    r = clf.classify(_factors(trend_strength=0.5, volatility_regime=0.3))
    assert r.regime == "trending_up"


def test_missing_factors_treated_as_neutral():
    clf = RegimeClassifier()
    # Empty dict → ts=0, vr=0.5 → fallback ranging
    r = clf.classify({})
    assert r.regime == "ranging"


# ---------------------------------------------------------------------------
# classify_and_store — DB integration
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_classify_and_store_writes_snapshot(session):
    clf = RegimeClassifier()
    at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    r = clf.classify_and_store(
        session=session,
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        open_time=at,
        factor_snapshot_id=42,
        factors=_factors(trend_strength=0.85),
    )
    assert r.regime == "trending_up"

    rows = session.execute(select(RegimeSnapshot)).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.regime == "trending_up"
    assert row.account_id == 1
    # factor_snapshot_id stashed in features JSON until migration adds the column.
    assert row.features["factor_snapshot_id"] == 42


def test_classify_and_store_is_idempotent_per_key(session):
    """Rerunning on the same (account, symbol, tf, time) replaces the row."""
    clf = RegimeClassifier()
    at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    clf.classify_and_store(
        session=session, account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", open_time=at,
        factor_snapshot_id=1, factors=_factors(trend_strength=0.85),
    )
    clf.classify_and_store(
        session=session, account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", open_time=at,
        factor_snapshot_id=2, factors=_factors(trend_strength=-0.85),
    )
    rows = session.execute(
        select(RegimeSnapshot).where(
            RegimeSnapshot.symbol == "BTCUSDT",
            RegimeSnapshot.snapshot_at == at,
        )
    ).scalars().all()
    assert len(rows) == 1
    # Latest one wins.
    assert rows[0].regime == "trending_down"
    assert rows[0].features["factor_snapshot_id"] == 2
