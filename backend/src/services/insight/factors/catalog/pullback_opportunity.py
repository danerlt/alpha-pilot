"""pullback_opportunity ∈ [0, 1].

Measures "is this a healthy pullback in an uptrend" — unsigned magnitude.

Requires:
  - EMA 20 > 50 > 200  (established uptrend)
  - last_close between EMA50 and EMA20  (pulled back but not broken)
  - RSI in [40, 60]  (healthy, not deeply oversold nor overheated)

Score:
  depth = (ema20 - last_close) / (ema20 - ema50)   # 0 at ema20, 1 at ema50
  rsi_bonus = 1 - |rsi - 50| / 10                   # 1 at 50, 0 at 40 or 60
  result = clamp(depth * 0.6 + rsi_bonus * 0.4, 0, 1)

If any precondition fails → 0.

Rationale: we want to buy dips in uptrends, not catch falling knives.
"""
from __future__ import annotations

from src.services.insight.factors.context import FactorContext


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


class PullbackOpportunity:
    name = "pullback_opportunity"
    version = 1

    def compute(self, ctx: FactorContext) -> float:
        ind = ctx.indicators
        if (
            ind.ema20 is None or ind.ema50 is None or ind.ema200 is None
            or ind.rsi is None
        ):
            return 0.0
        if ctx.candles.empty or "close" not in ctx.candles.columns:
            return 0.0

        # Uptrend precondition.
        if not (ind.ema20 > ind.ema50 > ind.ema200):
            return 0.0

        last_close = float(ctx.candles["close"].iloc[-1])
        # Must have pulled back (below EMA20) but not broken the uptrend
        # (still above EMA50). Also require the EMA gap to be meaningful.
        if not (ind.ema50 < last_close < ind.ema20):
            return 0.0
        if ind.ema20 - ind.ema50 <= 0:
            return 0.0

        # RSI precondition.
        if not (40.0 <= ind.rsi <= 60.0):
            return 0.0

        depth = (ind.ema20 - last_close) / (ind.ema20 - ind.ema50)
        rsi_bonus = 1.0 - abs(ind.rsi - 50.0) / 10.0
        return _clamp(depth * 0.6 + rsi_bonus * 0.4)
