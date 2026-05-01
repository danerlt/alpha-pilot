"""IndicatorComputer — compute technical indicators from candles, persist snapshots.

Input:  account_id + symbol + timeframe (reads from `candles` table)
Output: IndicatorValues + indicator_snapshots row id

Replaces the legacy `services/indicators/calculator.py` module with the new
Plan 1 multi-tenant schema (account_id required, no implicit tenant).

Indicators computed (pandas-ta):
- EMA 20 / 50 / 200
- RSI(14)
- MACD(12, 26, 9) → (macd, signal, hist)
- ATR(14)
- Bollinger Bands(20, 2) → (lower, middle, upper)
- Volume SMA(20)
- 20-bar returns stdev (volatility proxy)

`is_valid_for_trading()` returns True iff ATR and EMA20 are populated — these
are the minimum required by the risk/stop-loss logic downstream.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import pandas_ta as ta
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.candle import Candle
from src.models.indicator import IndicatorSnapshot

logger = logging.getLogger(__name__)

# EMA200 needs at least 200 rows; +10 buffer for indicator warm-up.
MIN_CANDLES_FOR_FULL_INDICATORS = 210


@dataclass
class IndicatorValues:
    ema20: float | None = None
    ema50: float | None = None
    ema200: float | None = None
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    atr: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    volume_ma: float | None = None
    volatility: float | None = None  # 20-bar returns stdev

    def is_valid_for_trading(self) -> bool:
        """True iff ATR and EMA20 are populated (minimum risk-management requirement)."""
        return self.atr is not None and self.ema20 is not None


def _safe_float(val) -> float | None:
    """Convert numpy/pandas numeric to Python float; return None for NaN / None / non-numeric."""
    try:
        if val is None:
            return None
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _compute_from_df(df: pd.DataFrame) -> IndicatorValues:
    """Pure function: given an OHLCV DataFrame, compute all indicators.

    Exposed for testability — unit tests don't need a DB to exercise the math.
    """
    if df.empty or len(df) < 20:
        return IndicatorValues()

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    result = IndicatorValues()

    # EMA
    result.ema20 = _safe_float(ta.ema(close, length=20).iloc[-1])
    if len(df) >= 50:
        result.ema50 = _safe_float(ta.ema(close, length=50).iloc[-1])
    if len(df) >= 200:
        result.ema200 = _safe_float(ta.ema(close, length=200).iloc[-1])

    # RSI(14)
    result.rsi = _safe_float(ta.rsi(close, length=14).iloc[-1])

    # MACD(12, 26, 9)
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        # pandas-ta column order: MACD, MACDh (histogram), MACDs (signal)
        result.macd = _safe_float(macd_df.iloc[-1, 0])
        result.macd_signal = _safe_float(macd_df.iloc[-1, 2])
        result.macd_hist = _safe_float(macd_df.iloc[-1, 1])

    # ATR(14)
    result.atr = _safe_float(ta.atr(high, low, close, length=14).iloc[-1])

    # Bollinger Bands(20, 2)
    bb = ta.bbands(close, length=20, std=2)
    if bb is not None and not bb.empty:
        # pandas-ta column order: BBL, BBM, BBU, BBB, BBP
        result.bb_lower = _safe_float(bb.iloc[-1, 0])
        result.bb_middle = _safe_float(bb.iloc[-1, 1])
        result.bb_upper = _safe_float(bb.iloc[-1, 2])

    # Volume SMA(20)
    result.volume_ma = _safe_float(ta.sma(volume, length=20).iloc[-1])

    # Volatility: 20-bar returns standard deviation.
    if len(df) >= 21:
        returns = close.pct_change().dropna()
        result.volatility = _safe_float(returns.tail(20).std())

    return result


def _candles_to_df(candles: list[Candle]) -> pd.DataFrame:
    """Convert SQLAlchemy Candle rows (oldest → newest) to an OHLCV DataFrame."""
    if not candles:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    data = {
        "open_time": [c.open_time for c in candles],
        "open": [float(c.open) for c in candles],
        "high": [float(c.high) for c in candles],
        "low": [float(c.low) for c in candles],
        "close": [float(c.close) for c in candles],
        "volume": [float(c.volume) for c in candles],
    }
    df = pd.DataFrame(data).set_index("open_time")
    return df


class IndicatorComputer:
    def __init__(self, session: Session):
        self._session = session

    def compute(
        self,
        *,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        limit: int = MIN_CANDLES_FOR_FULL_INDICATORS,
    ) -> tuple[IndicatorValues, int | None]:
        """Fetch the most recent `limit` candles, compute indicators, persist snapshot.

        Returns (values, snapshot_id). `snapshot_id` is None when there aren't
        enough candles to compute the minimum set — callers should treat this
        as "skip this cycle, wait for more data".
        """
        candles = self._session.execute(
            select(Candle)
            .where(
                Candle.account_id == account_id,
                Candle.trading_mode == trading_mode,
                Candle.symbol == symbol,
                Candle.timeframe == timeframe,
            )
            .order_by(Candle.open_time.desc())
            .limit(limit)
        ).scalars().all()

        if len(candles) < 20:
            logger.warning(
                "Not enough candles to compute indicators for %s %s (got %d < 20)",
                symbol, timeframe, len(candles),
            )
            return IndicatorValues(), None

        # DB returned newest→oldest; reverse so pandas-ta sees time-forward.
        candles_chrono = list(reversed(candles))
        df = _candles_to_df(candles_chrono)
        values = _compute_from_df(df)

        latest_open_time = candles_chrono[-1].open_time
        snapshot = IndicatorSnapshot(
            account_id=account_id,
            trading_mode=trading_mode,
            symbol=symbol,
            timeframe=timeframe,
            snapshot_at=latest_open_time,
            ema20=values.ema20,
            ema50=values.ema50,
            ema200=values.ema200,
            rsi=values.rsi,
            macd=values.macd,
            macd_signal=values.macd_signal,
            macd_hist=values.macd_hist,
            atr=values.atr,
            bb_upper=values.bb_upper,
            bb_middle=values.bb_middle,
            bb_lower=values.bb_lower,
            volume_ma=values.volume_ma,
            volatility=values.volatility,
        )
        self._session.add(snapshot)
        self._session.flush()
        snapshot_id = snapshot.id

        logger.info(
            "Indicator snapshot stored id=%s for %s %s: rsi=%.2f atr=%.6f",
            snapshot_id, symbol, timeframe,
            values.rsi or 0.0, values.atr or 0.0,
        )
        return values, snapshot_id
