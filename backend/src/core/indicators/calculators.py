"""无状态技术指标计算器 — 不依赖 DB / Session, 输入 OHLCV DataFrame, 输出 IndicatorValues。

业务流程层 (services/insight/indicators/computer.py) 负责取数据 + 持久化,
本模块只负责数学计算, 便于单元测试和 V1 回测引擎复用。

指标 (pandas-ta):
- EMA 20 / 50 / 200
- RSI(14)
- MACD(12, 26, 9) -> (macd, signal, hist)
- ATR(14)
- Bollinger Bands(20, 2) -> (lower, middle, upper)
- Volume SMA(20)
- 20-bar returns stdev (volatility proxy)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd
import pandas_ta as ta


# EMA200 至少要 200 行; +10 缓冲做 indicator warm-up
MIN_CANDLES_FOR_FULL_INDICATORS = 210


@dataclass
class IndicatorValues:
    """指标快照值 — 全部字段 None 表示该指标不足以计算 (数据不够 / 数学异常)。"""

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
        """ATR 与 EMA20 都齐 -> 满足风控/止损的最低要求。"""
        return self.atr is not None and self.ema20 is not None


def safe_float(val) -> float | None:
    """numpy/pandas 数值 -> Python float; NaN / None / 非数值 -> None。"""
    try:
        if val is None:
            return None
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def compute_indicators(df: pd.DataFrame) -> IndicatorValues:
    """纯函数: 输入 OHLCV DataFrame (列: open/high/low/close/volume), 输出 IndicatorValues。

    时间方向假设 oldest -> newest (即 df.iloc[-1] 是最新一根)。
    """
    if df.empty or len(df) < 20:
        return IndicatorValues()

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    result = IndicatorValues()

    # EMA
    result.ema20 = safe_float(ta.ema(close, length=20).iloc[-1])
    if len(df) >= 50:
        result.ema50 = safe_float(ta.ema(close, length=50).iloc[-1])
    if len(df) >= 200:
        result.ema200 = safe_float(ta.ema(close, length=200).iloc[-1])

    # RSI(14)
    result.rsi = safe_float(ta.rsi(close, length=14).iloc[-1])

    # MACD(12, 26, 9)
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        # pandas-ta 列序: MACD, MACDh (histogram), MACDs (signal)
        result.macd = safe_float(macd_df.iloc[-1, 0])
        result.macd_signal = safe_float(macd_df.iloc[-1, 2])
        result.macd_hist = safe_float(macd_df.iloc[-1, 1])

    # ATR(14)
    result.atr = safe_float(ta.atr(high, low, close, length=14).iloc[-1])

    # Bollinger Bands(20, 2)
    bb = ta.bbands(close, length=20, std=2)
    if bb is not None and not bb.empty:
        # pandas-ta 列序: BBL, BBM, BBU, BBB, BBP
        result.bb_lower = safe_float(bb.iloc[-1, 0])
        result.bb_middle = safe_float(bb.iloc[-1, 1])
        result.bb_upper = safe_float(bb.iloc[-1, 2])

    # Volume SMA(20)
    result.volume_ma = safe_float(ta.sma(volume, length=20).iloc[-1])

    # Volatility: 20-bar returns 标准差
    if len(df) >= 21:
        returns = close.pct_change().dropna()
        result.volatility = safe_float(returns.tail(20).std())

    return result
