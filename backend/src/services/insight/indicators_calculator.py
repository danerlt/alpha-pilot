"""技术指标计算服务 — 基于 pandas-ta 计算 EMA/RSI/MACD/ATR/布林带/波动率。"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import pandas_ta as ta
from sqlalchemy.orm import Session

from src.services.execution.candle_service import get_candle_df
from src.shared.config import get_settings
from src.models.indicator import IndicatorSnapshot

logger = logging.getLogger(__name__)

MIN_CANDLES = 210  # EMA200 需要至少 200 根 K 线


@dataclass
class IndicatorResult:
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
    volatility: float | None = None  # 20根K线收益率标准差

    def is_valid(self) -> bool:
        """校验核心指标是否计算成功（止损/风控必需）。"""
        return self.atr is not None and self.ema20 is not None


def _safe_float(val) -> float | None:
    try:
        if val is None:
            return None
        f = float(val)
        import math
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def calculate_indicators(df: pd.DataFrame) -> IndicatorResult:
    """对给定 OHLCV DataFrame 计算全套技术指标。"""
    if df.empty or len(df) < 20:
        logger.warning("Not enough candles to calculate indicators: %d rows", len(df))
        return IndicatorResult()

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    result = IndicatorResult()

    # EMA
    result.ema20 = _safe_float(ta.ema(close, length=20).iloc[-1])
    result.ema50 = _safe_float(ta.ema(close, length=50).iloc[-1]) if len(df) >= 50 else None
    result.ema200 = _safe_float(ta.ema(close, length=200).iloc[-1]) if len(df) >= 200 else None

    # RSI(14)
    result.rsi = _safe_float(ta.rsi(close, length=14).iloc[-1])

    # MACD(12,26,9)
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        result.macd = _safe_float(macd_df.iloc[-1, 0])        # MACD_12_26_9
        result.macd_signal = _safe_float(macd_df.iloc[-1, 2]) # MACDs_12_26_9
        result.macd_hist = _safe_float(macd_df.iloc[-1, 1])   # MACDh_12_26_9

    # ATR(14)
    result.atr = _safe_float(ta.atr(high, low, close, length=14).iloc[-1])

    # Bollinger Bands(20, 2)
    bb = ta.bbands(close, length=20, std=2)
    if bb is not None and not bb.empty:
        # pandas-ta column order: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB, BBP
        result.bb_lower = _safe_float(bb.iloc[-1, 0])   # BBL
        result.bb_middle = _safe_float(bb.iloc[-1, 1])  # BBM
        result.bb_upper = _safe_float(bb.iloc[-1, 2])   # BBU

    # Volume MA(20)
    result.volume_ma = _safe_float(ta.sma(volume, length=20).iloc[-1])

    # Volatility: 20根K线收益率标准差（年化因子不乘，仅相对比较用）
    if len(df) >= 20:
        returns = close.pct_change().dropna()
        result.volatility = _safe_float(returns.tail(20).std())

    return result


def compute_and_store(
    db: Session,
    symbol: str,
    timeframe: str,
    limit: int = MIN_CANDLES,
) -> IndicatorSnapshot | None:
    """从 DB 拉取 K 线 → 计算指标 → 写入 indicator_snapshots。"""
    settings = get_settings()
    df = get_candle_df(db, symbol, timeframe, limit=limit)
    if df.empty:
        logger.warning("No candle data in DB for %s %s", symbol, timeframe)
        return None

    result = calculate_indicators(df)

    snapshot = IndicatorSnapshot(
        trading_mode=settings.TRADING_MODE.value,
        symbol=symbol,
        timeframe=timeframe,
        snapshot_at=datetime.now(tz=timezone.utc),
        ema20=result.ema20,
        ema50=result.ema50,
        ema200=result.ema200,
        rsi=result.rsi,
        macd=result.macd,
        macd_signal=result.macd_signal,
        macd_hist=result.macd_hist,
        atr=result.atr,
        bb_upper=result.bb_upper,
        bb_middle=result.bb_middle,
        bb_lower=result.bb_lower,
        volume_ma=result.volume_ma,
        volatility=result.volatility,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    logger.info(
        "Indicator snapshot saved for %s %s: RSI=%.2f ATR=%.4f",
        symbol,
        timeframe,
        result.rsi or 0,
        result.atr or 0,
    )
    return snapshot


def get_latest_indicators(db: Session, symbol: str, timeframe: str) -> IndicatorSnapshot | None:
    """返回最新的指标快照。"""
    settings = get_settings()
    return (
        db.query(IndicatorSnapshot)
        .filter(
            IndicatorSnapshot.trading_mode == settings.TRADING_MODE.value,
            IndicatorSnapshot.symbol == symbol,
            IndicatorSnapshot.timeframe == timeframe,
        )
        .order_by(IndicatorSnapshot.snapshot_at.desc())
        .first()
    )
