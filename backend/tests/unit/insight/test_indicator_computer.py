"""Unit tests for IndicatorComputer (Plan 2 Task A1)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.models import Base, Candle
from src.services.insight.indicators.computer import (
    IndicatorComputer,
    _compute_from_df,
)

# ---------------------------------------------------------------------------
# Pure-function tests — no DB required
# ---------------------------------------------------------------------------

def _synthetic_ohlcv(closes: list[float]) -> pd.DataFrame:
    """Build an OHLCV DataFrame from a list of closes.

    High/low are small spreads around close; volume is constant-ish. Good
    enough for indicator math tests.
    """
    data = []
    for i, c in enumerate(closes):
        data.append({
            "open": c * 0.999,
            "high": c * 1.002,
            "low": c * 0.998,
            "close": c,
            "volume": 1000.0 + (i % 10) * 10,
        })
    idx = pd.date_range(
        start="2026-01-01", periods=len(closes), freq="1h", tz="UTC",
    )
    return pd.DataFrame(data, index=idx)


def test_compute_returns_all_none_when_df_too_small():
    df = _synthetic_ohlcv([100, 101, 102])  # only 3 bars
    values = _compute_from_df(df)
    assert values.ema20 is None
    assert values.atr is None
    assert not values.is_valid_for_trading()


def test_compute_on_uptrend_produces_ema_stack_ordered_upward():
    """In a steady uptrend the most-reactive EMA should be highest.

    closes linear from 100→350 over 250 bars: price climbing => EMA20 > EMA50 > EMA200.
    """
    closes = [100.0 + i for i in range(250)]
    df = _synthetic_ohlcv(closes)
    values = _compute_from_df(df)

    assert values.ema20 is not None
    assert values.ema50 is not None
    assert values.ema200 is not None
    # Uptrend: shorter EMAs lag less, so they sit above longer ones.
    assert values.ema20 > values.ema50 > values.ema200
    assert values.is_valid_for_trading()
    assert values.atr > 0
    # RSI should reflect the monotonic uptrend and sit above 50.
    assert values.rsi is not None and values.rsi > 50


def test_compute_on_downtrend_inverts_ema_stack():
    closes = [350.0 - i for i in range(250)]
    df = _synthetic_ohlcv(closes)
    values = _compute_from_df(df)
    assert values.ema20 is not None
    assert values.ema20 < values.ema50 < values.ema200
    assert values.rsi is not None and values.rsi < 50


def test_compute_macd_histogram_positive_on_acceleration():
    """An accelerating uptrend → MACD histogram (MACD - signal) > 0."""
    # Accelerating curve so fast EMA rises faster than slow EMA.
    closes = [100.0 + i * 1.0 + (i / 50) ** 2 for i in range(220)]
    df = _synthetic_ohlcv(closes)
    values = _compute_from_df(df)
    assert values.macd_hist is not None
    assert values.macd_hist > 0


def test_compute_bollinger_bands_enclose_last_close():
    closes = [100.0 + (i * 0.5) for i in range(60)]
    df = _synthetic_ohlcv(closes)
    values = _compute_from_df(df)
    last_close = closes[-1]
    # BB use 2-sigma envelope — with small noise the last close is inside.
    assert values.bb_lower is not None
    assert values.bb_upper is not None
    assert values.bb_lower < last_close < values.bb_upper
    assert values.bb_lower < values.bb_middle < values.bb_upper


def test_compute_volatility_zero_on_flat_prices_is_near_zero():
    closes = [100.0] * 50
    df = _synthetic_ohlcv(closes)
    values = _compute_from_df(df)
    assert values.volatility is not None
    assert values.volatility < 1e-6  # effectively zero


# ---------------------------------------------------------------------------
# DB integration tests (SQLite in-memory)
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _seed_candles(
    session: Session,
    *,
    n: int,
    account_id: int = 1,
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    start_price: float = 100.0,
    price_step: float = 1.0,
):
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(n):
        price = start_price + i * price_step
        c = Candle(
            account_id=account_id,
            trading_mode="testnet",
            symbol=symbol,
            timeframe=timeframe,
            open_time=base_time + timedelta(hours=i),
            open=price * 0.999,
            high=price * 1.002,
            low=price * 0.998,
            close=price,
            volume=1000.0,
        )
        session.add(c)
    session.flush()


def test_compute_returns_none_snapshot_when_not_enough_candles(session):
    _seed_candles(session, n=5)  # too few for indicators
    computer = IndicatorComputer(session)
    values, snapshot_id = computer.compute(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
    )
    assert snapshot_id is None
    assert values.ema20 is None
    # No snapshot written.
    from src.models import IndicatorSnapshot
    assert session.query(IndicatorSnapshot).count() == 0


def test_compute_writes_indicator_snapshot_row(session):
    n = 250
    _seed_candles(session, n=n, start_price=100.0, price_step=1.0)
    computer = IndicatorComputer(session)
    values, snapshot_id = computer.compute(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
    )
    assert snapshot_id is not None
    assert values.is_valid_for_trading()

    from src.models import IndicatorSnapshot
    row = session.get(IndicatorSnapshot, snapshot_id)
    assert row is not None
    assert row.account_id == 1
    assert row.trading_mode == "testnet"
    assert row.symbol == "BTCUSDT"
    assert row.timeframe == "1h"
    # snapshot_at should equal the latest candle's open_time. SQLite discards
    # tzinfo so compare as naive UTC values.
    expected_naive = (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=n - 1)).replace(tzinfo=None)
    actual = row.snapshot_at.replace(tzinfo=None) if row.snapshot_at.tzinfo else row.snapshot_at
    assert actual == expected_naive


def test_compute_snapshot_at_matches_latest_candle(session):
    n = 250
    _seed_candles(session, n=n)
    computer = IndicatorComputer(session)
    _, snapshot_id = computer.compute(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
    )
    from src.models import IndicatorSnapshot
    row = session.get(IndicatorSnapshot, snapshot_id)
    expected_naive = (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=n - 1)).replace(tzinfo=None)
    actual = row.snapshot_at.replace(tzinfo=None) if row.snapshot_at.tzinfo else row.snapshot_at
    assert actual == expected_naive


def test_compute_only_uses_candles_for_same_account(session):
    """account_id filter must exclude other tenants' candles.

    The candles table has a UNIQUE constraint on (symbol, timeframe, open_time)
    that doesn't include account_id (legacy schema artifact), so we use a
    different symbol for the other tenant to avoid the collision.
    """
    _seed_candles(session, n=250, account_id=1, symbol="BTCUSDT")
    _seed_candles(session, n=50, account_id=2, symbol="ETHUSDT", start_price=9999.0)

    computer = IndicatorComputer(session)
    values, _ = computer.compute(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
    )
    # If account 2's high prices leaked in, EMA would be much bigger than the
    # tail of account 1's linear 100→349 series.
    assert values.ema20 is not None
    assert values.ema20 < 500  # account 1 tail is ~349

    # Sanity: asking for account 2's ETHUSDT candles gets values around 9999+.
    values2, _ = computer.compute(
        account_id=2, trading_mode="testnet",
        symbol="ETHUSDT", timeframe="1h",
    )
    # Only 50 bars for account 2 — ema200 is None, ema20 available.
    assert values2.ema20 is not None
    assert values2.ema20 > 9000
