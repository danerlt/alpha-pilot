"""trend_strength ∈ [-1, 1].

Signed strength of the prevailing trend:

  base = clamp(sign(ema20 - ema50) * |ema20 - ema50| / (atr * 2), -1, 1)
  bonus = +0.2 if EMA 20 > 50 > 200 (bullish stack)
          -0.2 if EMA 20 < 50 < 200 (bearish stack)
          0 otherwise

Result = clamp(base + bonus, -1, 1).

Rationale: the EMA gap normalized by ATR measures trend strength in
"volatility units"; the alignment bonus rewards clean stacks.

Returns 0.0 when EMA20 or ATR isn't available.
"""
from __future__ import annotations

from src.insight.factors.context import FactorContext


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


class TrendStrength:
    name = "trend_strength"
    version = 1

    def compute(self, ctx: FactorContext) -> float:
        ind = ctx.indicators
        if ind.ema20 is None or ind.ema50 is None or ind.atr is None or ind.atr <= 0:
            return 0.0

        diff = ind.ema20 - ind.ema50
        sign = 1.0 if diff > 0 else (-1.0 if diff < 0 else 0.0)
        base = sign * min(1.0, abs(diff) / (ind.atr * 2.0))

        bonus = 0.0
        if ind.ema200 is not None:
            if ind.ema20 > ind.ema50 > ind.ema200:
                bonus = 0.2
            elif ind.ema20 < ind.ema50 < ind.ema200:
                bonus = -0.2

        return _clamp(base + bonus)
