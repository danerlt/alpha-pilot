"""volume_confirmation ∈ [0, 1].

Current bar volume relative to the 20-bar SMA:

  ratio = current_volume / volume_ma
  result = clamp(ratio - 1.0, 0, 1)  # only count expansion, not contraction

So a 1x volume gives 0, 2x gives 1.0 (capped), below-average gives 0.

Rationale: for a long signal we want expansion — shrinking volume is neutral
to negative, so we clamp it to 0 (this factor is an "add evidence" input,
not a counter-signal).

Returns 0.0 when volume_ma is missing / zero.
"""
from __future__ import annotations

from src.services.insight.factors.context import FactorContext


class VolumeConfirmation:
    name = "volume_confirmation"
    version = 1

    def compute(self, ctx: FactorContext) -> float:
        ind = ctx.indicators
        if ind.volume_ma is None or ind.volume_ma <= 0:
            return 0.0
        if ctx.candles.empty or "volume" not in ctx.candles.columns:
            return 0.0

        current_volume = float(ctx.candles["volume"].iloc[-1])
        ratio = current_volume / ind.volume_ma
        return max(0.0, min(1.0, ratio - 1.0))
