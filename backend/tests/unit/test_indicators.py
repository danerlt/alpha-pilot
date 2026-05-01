"""单元测试：技术指标计算 (indicators/calculator.py)。"""
import math

import pandas as pd
import pytest

from src.services.insight.indicators_calculator import IndicatorResult, calculate_indicators, _safe_float


# ─── 测试辅助 ─────────────────────────────────────────────────────────────────

def _make_df(n: int, base_price: float = 100.0, volume: float = 1000.0) -> pd.DataFrame:
    """生成 n 根简单 OHLCV K 线（价格微小波动）。"""
    import numpy as np
    rng = np.random.default_rng(42)
    closes = base_price + rng.normal(0, base_price * 0.01, n).cumsum()
    closes = closes.clip(base_price * 0.5, base_price * 2.0)
    highs = closes * (1 + abs(rng.normal(0, 0.005, n)))
    lows = closes * (1 - abs(rng.normal(0, 0.005, n)))
    opens = closes * (1 + rng.normal(0, 0.003, n))
    volumes = rng.uniform(volume * 0.5, volume * 1.5, n)
    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


# ─── _safe_float ──────────────────────────────────────────────────────────────

def test_safe_float_with_normal_value():
    assert _safe_float(42.5) == pytest.approx(42.5)


def test_safe_float_with_nan_returns_none():
    assert _safe_float(float("nan")) is None


def test_safe_float_with_none_returns_none():
    assert _safe_float(None) is None


def test_safe_float_with_string_number():
    assert _safe_float("3.14") == pytest.approx(3.14)


# ─── 空/不足数据 ──────────────────────────────────────────────────────────────

def test_empty_df_returns_empty_result():
    result = calculate_indicators(pd.DataFrame())
    assert result.ema20 is None
    assert result.rsi is None
    assert not result.is_valid()


def test_too_few_candles_returns_empty_result():
    df = _make_df(10)
    result = calculate_indicators(df)
    assert result.ema20 is None
    assert not result.is_valid()


# ─── 足够数据 (20-49 根) ──────────────────────────────────────────────────────

def test_20_candles_computes_ema20_and_rsi():
    df = _make_df(20)
    result = calculate_indicators(df)
    assert result.ema20 is not None
    assert result.rsi is not None
    assert result.ema50 is None   # 需要 50 根
    assert result.ema200 is None  # 需要 200 根
    assert result.is_valid()  # ema20 + atr 已可用


def test_20_candles_atr_not_none():
    df = _make_df(30)
    result = calculate_indicators(df)
    assert result.atr is not None
    assert result.atr > 0


def test_20_candles_bollinger_bands():
    df = _make_df(25)
    result = calculate_indicators(df)
    if result.bb_upper is not None:
        assert result.bb_upper > result.bb_middle > result.bb_lower


# ─── 50 根 K 线 ───────────────────────────────────────────────────────────────

def test_50_candles_computes_ema50():
    df = _make_df(60)
    result = calculate_indicators(df)
    assert result.ema20 is not None
    assert result.ema50 is not None
    assert result.ema200 is None


# ─── 200 根 K 线 ──────────────────────────────────────────────────────────────

def test_200_candles_computes_all_emas():
    df = _make_df(210)
    result = calculate_indicators(df)
    assert result.ema20 is not None
    assert result.ema50 is not None
    assert result.ema200 is not None
    assert result.rsi is not None
    assert result.macd is not None
    assert result.macd_signal is not None
    assert result.atr is not None
    assert result.volume_ma is not None
    assert result.volatility is not None


def test_is_valid_with_full_data():
    df = _make_df(210)
    result = calculate_indicators(df)
    assert result.is_valid()


# ─── RSI 值域 ─────────────────────────────────────────────────────────────────

def test_rsi_in_range():
    df = _make_df(100)
    result = calculate_indicators(df)
    if result.rsi is not None:
        assert 0 <= result.rsi <= 100


# ─── 趋势市场 EMA 排列 ────────────────────────────────────────────────────────

def test_uptrend_ema_ordering():
    """在明显上涨趋势中，EMA20 应高于 EMA50（近期反应更快）。"""
    import numpy as np
    n = 210
    prices = np.linspace(100, 300, n)  # 完全线性上涨
    df = pd.DataFrame({
        "open":   prices,
        "high":   prices * 1.005,
        "low":    prices * 0.995,
        "close":  prices,
        "volume": [1000.0] * n,
    })
    result = calculate_indicators(df)
    assert result.ema20 is not None
    assert result.ema50 is not None
    assert result.ema200 is not None
    # 上涨趋势中，短期 EMA > 长期 EMA
    assert result.ema20 > result.ema50 > result.ema200


# ─── IndicatorResult is_valid ─────────────────────────────────────────────────

def test_is_valid_requires_ema20_and_atr():
    r = IndicatorResult()
    assert not r.is_valid()

    r.ema20 = 100.0
    assert not r.is_valid()  # still missing atr

    r.atr = 1.5
    assert r.is_valid()
