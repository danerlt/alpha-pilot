"""breakout_validity ∈ [-1, 1].

Scores how "real" a breakout looks:

  last_close vs bb_upper:
    - above bb_upper AND volume > 1.3x volume_ma  → +0.7  (valid breakout)
    - above bb_upper but weak volume               → +0.3  (suspect breakout)
    - in middle band                                →  0.0
    - below bb_lower AND volume > 1.3x volume_ma   → -0.7  (breakdown)

  post-breakout follow-through adjustment:
    if last_close > bb_upper but previous 3 bars had one that broke back
    below bb_middle → subtract 0.4 (false breakout fade)

Rationale: breakouts without volume are usually short-lived; a recent
"tap and reject" suggests the breakout is losing validity.

Returns 0.0 when Bollinger Bands, volume_ma, or candles are missing.
"""
from __future__ import annotations

from src.insight.factors.context import FactorContext


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


class BreakoutValidity:
    name = "breakout_validity"
    version = 1

    def compute(self, ctx: FactorContext) -> float:
        ind = ctx.indicators
        if (
            ind.bb_upper is None or ind.bb_lower is None or ind.bb_middle is None
            or ind.volume_ma is None or ind.volume_ma <= 0
        ):
            return 0.0

        if ctx.candles.empty or len(ctx.candles) < 4:
            return 0.0

        last_close = float(ctx.candles["close"].iloc[-1])
        last_volume = float(ctx.candles["volume"].iloc[-1])
        vol_ratio = last_volume / ind.volume_ma

        base = 0.0
        if last_close > ind.bb_upper:
            base = 0.7 if vol_ratio > 1.3 else 0.3
        elif last_close < ind.bb_lower:
            base = -0.7 if vol_ratio > 1.3 else -0.3

        # False-breakout fade: if any of the previous 3 closes was below
        # bb_middle after having touched bb_upper, trim the bullish signal.
        if base > 0:
            closes = ctx.candles["close"].iloc[-4:-1]  # previous 3 bars (exclude current)
            if (closes < ind.bb_middle).any():
                base -= 0.4

        return _clamp(base)
