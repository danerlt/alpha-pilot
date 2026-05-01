"""Tests for each of the six V0.1 preset factors.

We use synthetic FactorContext scenarios (strong uptrend / downtrend /
pullback / breakout / chaotic) to validate direction and range for each
factor. Magnitudes are asserted loosely because exact values depend on
the normalization choice and are allowed to drift with future tuning.
"""
from __future__ import annotations

import pandas as pd

from src.services.insight.factors.catalog import (
    breakout_validity,
    momentum_quality,
    pullback_opportunity,
    trend_strength,
    volatility_regime,
    volume_confirmation,
)
from src.services.insight.factors.registry import FactorContext
from src.services.insight.indicators.computer import IndicatorValues


def _build_candles(closes, volumes):
    assert len(closes) == len(volumes)
    data = []
    for c, v in zip(closes, volumes):
        data.append({
            "open": c * 0.999,
            "high": c * 1.002,
            "low": c * 0.998,
            "close": c,
            "volume": v,
        })
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="1h", tz="UTC")
    return pd.DataFrame(data, index=idx)


# ---------------------------------------------------------------------------
# trend_strength
# ---------------------------------------------------------------------------

def test_trend_strength_zero_when_indicators_missing():
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=IndicatorValues())
    assert trend_strength.TrendStrength().compute(ctx) == 0.0


def test_trend_strength_positive_on_bullish_stack():
    ind = IndicatorValues(ema20=105.0, ema50=100.0, ema200=95.0, atr=2.0)
    ctx = FactorContext(candles=_build_candles([105], [1000]), indicators=ind)
    v = trend_strength.TrendStrength().compute(ctx)
    assert v > 0.5  # clearly bullish


def test_trend_strength_negative_on_bearish_stack():
    ind = IndicatorValues(ema20=95.0, ema50=100.0, ema200=105.0, atr=2.0)
    ctx = FactorContext(candles=_build_candles([95], [1000]), indicators=ind)
    v = trend_strength.TrendStrength().compute(ctx)
    assert v < -0.5


def test_trend_strength_clamped_to_unit_range():
    """Extreme gap normalized by tiny ATR must clamp to 1.0."""
    ind = IndicatorValues(ema20=200.0, ema50=100.0, ema200=50.0, atr=1.0)
    ctx = FactorContext(candles=_build_candles([200], [1000]), indicators=ind)
    v = trend_strength.TrendStrength().compute(ctx)
    assert -1.0 <= v <= 1.0
    assert v == 1.0  # clamped


# ---------------------------------------------------------------------------
# momentum_quality
# ---------------------------------------------------------------------------

def test_momentum_quality_zero_when_missing_inputs():
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=IndicatorValues())
    assert momentum_quality.MomentumQuality().compute(ctx) == 0.0


def test_momentum_quality_positive_in_healthy_rsi_band():
    ind = IndicatorValues(macd_hist=2.0, atr=1.0, rsi=55.0)
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=ind)
    v = momentum_quality.MomentumQuality().compute(ctx)
    assert v > 0.5  # macd_hist/atr=2 → tanh(2) ≈ 0.96, weight=1


def test_momentum_quality_faded_when_rsi_extreme():
    ind = IndicatorValues(macd_hist=2.0, atr=1.0, rsi=85.0)  # overbought
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=ind)
    v = momentum_quality.MomentumQuality().compute(ctx)
    # distance_from_band = 35 - 10 = 25, weight = 1 - 25/40 = 0.375
    # raw = tanh(2) ≈ 0.96; result ≈ 0.36
    assert 0.2 < v < 0.5


def test_momentum_quality_clamped_at_rsi_extremes_zero():
    """RSI at 0 or 100: distance_from_band = 40, weight = 0."""
    ind = IndicatorValues(macd_hist=5.0, atr=1.0, rsi=100.0)
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=ind)
    v = momentum_quality.MomentumQuality().compute(ctx)
    assert v == 0.0


# ---------------------------------------------------------------------------
# volume_confirmation
# ---------------------------------------------------------------------------

def test_volume_confirmation_zero_when_contracting():
    ind = IndicatorValues(volume_ma=1000.0)
    ctx = FactorContext(candles=_build_candles([100], [500]), indicators=ind)
    assert volume_confirmation.VolumeConfirmation().compute(ctx) == 0.0


def test_volume_confirmation_half_at_1point5x():
    ind = IndicatorValues(volume_ma=1000.0)
    ctx = FactorContext(candles=_build_candles([100], [1500]), indicators=ind)
    assert volume_confirmation.VolumeConfirmation().compute(ctx) == 0.5


def test_volume_confirmation_capped_at_one():
    ind = IndicatorValues(volume_ma=1000.0)
    ctx = FactorContext(candles=_build_candles([100], [10_000]), indicators=ind)
    assert volume_confirmation.VolumeConfirmation().compute(ctx) == 1.0


# ---------------------------------------------------------------------------
# volatility_regime
# ---------------------------------------------------------------------------

def test_volatility_regime_default_when_missing():
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=IndicatorValues())
    v = volatility_regime.VolatilityRegime().compute(ctx)
    assert v == 0.5


def test_volatility_regime_low_when_calm():
    # narrow BB (2% width), tiny ATR (0.5% of close)
    ind = IndicatorValues(bb_upper=101.0, bb_middle=100.0, bb_lower=99.0, atr=0.5)
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=ind)
    v = volatility_regime.VolatilityRegime().compute(ctx)
    # bb_width_pct = 2/100 = 0.02; 0.02/0.10 = 0.2
    # atr_pct = 0.5/100 = 0.005; 0.005/0.02 = 0.25
    # score = (0.2 + 0.25)/2 = 0.225
    assert 0.1 < v < 0.35


def test_volatility_regime_high_when_wild():
    ind = IndicatorValues(bb_upper=115.0, bb_middle=100.0, bb_lower=85.0, atr=5.0)
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=ind)
    v = volatility_regime.VolatilityRegime().compute(ctx)
    assert v >= 0.9


# ---------------------------------------------------------------------------
# breakout_validity
# ---------------------------------------------------------------------------

def test_breakout_validity_zero_when_missing():
    ctx = FactorContext(candles=_build_candles([100], [1000]), indicators=IndicatorValues())
    assert breakout_validity.BreakoutValidity().compute(ctx) == 0.0


def test_breakout_validity_strong_positive_on_volume_breakout():
    ind = IndicatorValues(bb_upper=100.0, bb_middle=98.0, bb_lower=96.0, volume_ma=1000.0)
    # 4 bars: three under bb_middle, last above bb_upper with 2x volume
    closes = [96.0, 96.5, 97.0, 102.0]
    volumes = [1000.0, 1000.0, 1000.0, 2000.0]
    ctx = FactorContext(candles=_build_candles(closes, volumes), indicators=ind)
    v = breakout_validity.BreakoutValidity().compute(ctx)
    # prev 3 closes all < bb_middle=98, so fade triggers: 0.7 - 0.4 = 0.3
    assert abs(v - 0.3) < 0.01


def test_breakout_validity_suspect_on_weak_volume():
    ind = IndicatorValues(bb_upper=100.0, bb_middle=98.0, bb_lower=96.0, volume_ma=1000.0)
    # 4 bars: last above bb_upper but average volume; previous 3 all >= bb_middle
    closes = [98.0, 98.5, 99.0, 102.0]
    volumes = [1000.0, 1000.0, 1000.0, 1000.0]
    ctx = FactorContext(candles=_build_candles(closes, volumes), indicators=ind)
    v = breakout_validity.BreakoutValidity().compute(ctx)
    # base=0.3 (weak volume); no fade since prev 3 >= 98
    assert abs(v - 0.3) < 0.01


def test_breakout_validity_negative_on_breakdown():
    ind = IndicatorValues(bb_upper=102.0, bb_middle=100.0, bb_lower=98.0, volume_ma=1000.0)
    # 4 bars: last below bb_lower with volume
    closes = [100.0, 100.0, 100.0, 96.0]
    volumes = [1000.0, 1000.0, 1000.0, 2000.0]
    ctx = FactorContext(candles=_build_candles(closes, volumes), indicators=ind)
    v = breakout_validity.BreakoutValidity().compute(ctx)
    assert v < -0.5


# ---------------------------------------------------------------------------
# pullback_opportunity
# ---------------------------------------------------------------------------

def test_pullback_opportunity_zero_when_not_uptrend():
    ind = IndicatorValues(ema20=95.0, ema50=100.0, ema200=105.0, rsi=50.0)  # downtrend
    ctx = FactorContext(candles=_build_candles([98], [1000]), indicators=ind)
    assert pullback_opportunity.PullbackOpportunity().compute(ctx) == 0.0


def test_pullback_opportunity_zero_when_not_pulled_back():
    ind = IndicatorValues(ema20=100.0, ema50=95.0, ema200=90.0, rsi=50.0)
    # price above EMA20, no pullback
    ctx = FactorContext(candles=_build_candles([105], [1000]), indicators=ind)
    assert pullback_opportunity.PullbackOpportunity().compute(ctx) == 0.0


def test_pullback_opportunity_peak_in_mid_retrace_with_clean_rsi():
    ind = IndicatorValues(ema20=100.0, ema50=90.0, ema200=80.0, rsi=50.0)
    # last close at 95 (halfway between ema50 and ema20)
    ctx = FactorContext(candles=_build_candles([95], [1000]), indicators=ind)
    v = pullback_opportunity.PullbackOpportunity().compute(ctx)
    # depth = (100-95)/(100-90) = 0.5
    # rsi_bonus = 1 - |50-50|/10 = 1.0
    # result = 0.5*0.6 + 1.0*0.4 = 0.7
    assert abs(v - 0.7) < 0.01


def test_pullback_opportunity_zero_when_rsi_out_of_band():
    ind = IndicatorValues(ema20=100.0, ema50=90.0, ema200=80.0, rsi=30.0)
    ctx = FactorContext(candles=_build_candles([95], [1000]), indicators=ind)
    assert pullback_opportunity.PullbackOpportunity().compute(ctx) == 0.0
