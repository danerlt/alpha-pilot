"""Tests for FactorComputer — writes factor_snapshots rows with all six factors."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.models import Base, FactorSnapshot
from src.services.insight.factors.computer import FactorComputer
from src.services.insight.factors.registry import FactorRegistry
from src.services.insight.indicators.computer import IndicatorValues


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _make_candles():
    closes = [100.0 + i * 0.5 for i in range(30)]
    df = pd.DataFrame({
        "open": closes,
        "high": [c * 1.002 for c in closes],
        "low": [c * 0.998 for c in closes],
        "close": closes,
        "volume": [1000.0] * 30,
    }, index=pd.date_range("2026-01-01", periods=30, freq="1h", tz="UTC"))
    return df


def _sample_indicators():
    return IndicatorValues(
        ema20=110.0, ema50=105.0, ema200=100.0,
        rsi=55.0,
        macd=1.0, macd_signal=0.5, macd_hist=0.5,
        atr=1.0,
        bb_upper=115.0, bb_middle=110.0, bb_lower=105.0,
        volume_ma=1000.0,
        volatility=0.01,
    )


def test_compute_and_store_writes_row_with_all_factors(session):
    computer = FactorComputer(session)
    factors, snap_id = computer.compute_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        indicators=_sample_indicators(),
        candles_df=_make_candles(),
    )

    assert snap_id is not None
    # All six factors present.
    expected_names = {
        "trend_strength", "momentum_quality", "volume_confirmation",
        "volatility_regime", "breakout_validity", "pullback_opportunity",
    }
    assert set(factors) == expected_names
    for name, value in factors.items():
        assert isinstance(value, float), f"{name} must be float"

    row = session.get(FactorSnapshot, snap_id)
    assert row.account_id == 1
    assert row.symbol == "BTCUSDT"
    assert row.factors_json == factors
    assert set(row.factor_def_versions_json) == expected_names


def test_compute_and_store_is_idempotent_for_same_key(session):
    """Re-running on the same (account, symbol, tf, open_time) updates in place."""
    computer = FactorComputer(session)
    at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    _, first_id = computer.compute_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        open_time=at, indicators=_sample_indicators(),
        candles_df=_make_candles(),
    )
    _, second_id = computer.compute_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        open_time=at, indicators=_sample_indicators(),
        candles_df=_make_candles(),
    )

    # Second call deleted + inserted fresh; ID differs but only one row total.
    assert second_id is not None
    count = session.execute(
        select(FactorSnapshot).where(
            FactorSnapshot.symbol == "BTCUSDT",
            FactorSnapshot.open_time == at,
        )
    ).all()
    assert len(count) == 1


def test_compute_handles_factor_exception_by_substituting_zero(session):
    """A broken factor shouldn't poison the whole snapshot."""
    reg = FactorRegistry()

    class Broken:
        name = "boom"
        version = 1
        def compute(self, ctx):
            raise RuntimeError("kaboom")

    class Fine:
        name = "fine"
        version = 1
        def compute(self, ctx):
            return 0.42

    reg.register(Broken())
    reg.register(Fine())

    computer = FactorComputer(session, registry=reg)
    factors, _ = computer.compute_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        indicators=_sample_indicators(),
        candles_df=_make_candles(),
    )
    assert factors == {"boom": 0.0, "fine": 0.42}
