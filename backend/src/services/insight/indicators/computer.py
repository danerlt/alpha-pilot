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

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.indicators.calculators import (
    MIN_CANDLES_FOR_FULL_INDICATORS,
    IndicatorValues,
)
from src.core.indicators.calculators import (
    compute_indicators as _compute_from_df,
)
from src.models.candle import Candle
from src.models.indicator import IndicatorSnapshot

logger = logging.getLogger(__name__)

# 重导出以保持向后兼容 (旧测试 / 旧业务代码可能 import 这两个名字)
__all__ = ["IndicatorComputer", "IndicatorValues", "MIN_CANDLES_FOR_FULL_INDICATORS"]


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
