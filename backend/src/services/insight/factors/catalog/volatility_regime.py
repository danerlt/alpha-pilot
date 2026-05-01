"""volatility_regime ∈ [0, 1].

Magnitude of current volatility relative to a baseline (20-bar returns stdev).
Combines Bollinger Band width (price volatility) and ATR (range volatility):

  bb_width_pct = (bb_upper - bb_lower) / bb_middle   # relative BB width
  baseline     = max(volatility, 0.005)              # floor to avoid division blowup
  atr_pct      = atr / last_close

  score = (bb_width_pct / 0.10 + atr_pct / 0.02) / 2  # each term roughly [0, 1+]
  result = clamp(score, 0, 1)

Thresholds (0.10 BB width, 2% ATR pct) are calibrated for crypto majors
on 1h timeframe; acceptable starting defaults, tunable by the learning
controller later.

Returns 0.5 (ambiguous/default) when required inputs are missing — this
keeps downstream regime classification from treating missing data as
"calm" (which could permit risky opens).
"""
from __future__ import annotations

from src.services.insight.factors.context import FactorContext


class VolatilityRegime:
    name = "volatility_regime"
    version = 1

    def compute(self, ctx: FactorContext) -> float:
        ind = ctx.indicators
        if (
            ind.bb_upper is None or ind.bb_lower is None or ind.bb_middle is None
            or ind.atr is None or ind.bb_middle <= 0
        ):
            return 0.5

        if ctx.candles.empty or "close" not in ctx.candles.columns:
            return 0.5

        last_close = float(ctx.candles["close"].iloc[-1])
        if last_close <= 0:
            return 0.5

        bb_width_pct = (ind.bb_upper - ind.bb_lower) / ind.bb_middle
        atr_pct = ind.atr / last_close
        score = (bb_width_pct / 0.10 + atr_pct / 0.02) / 2.0
        return max(0.0, min(1.0, score))
