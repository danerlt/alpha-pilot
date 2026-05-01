"""momentum_quality ∈ [-1, 1].

MACD histogram normalized by ATR, weighted by RSI proximity to a healthy
50 ± 10 band:

  raw = tanh(macd_hist / atr)
  weight = 1.0 if 40 <= rsi <= 60
           else max(0.0, 1 - (|rsi - 50| - 10) / 40)  # fades to 0 at rsi=0 or 100
  result = raw * weight

Rationale: MACD momentum has real directional value only in the mid-RSI
range; extremes (overbought/oversold) mean the move is spent, so we fade
the signal.

Returns 0.0 if MACD hist, ATR, or RSI is missing.
"""
from __future__ import annotations

import math

from src.services.insight.factors.context import FactorContext


class MomentumQuality:
    name = "momentum_quality"
    version = 1

    def compute(self, ctx: FactorContext) -> float:
        ind = ctx.indicators
        if ind.macd_hist is None or ind.atr is None or ind.atr <= 0 or ind.rsi is None:
            return 0.0

        raw = math.tanh(ind.macd_hist / ind.atr)

        rsi = ind.rsi
        if 40.0 <= rsi <= 60.0:
            weight = 1.0
        else:
            distance_from_band = abs(rsi - 50.0) - 10.0
            weight = max(0.0, 1.0 - distance_from_band / 40.0)

        return raw * weight
