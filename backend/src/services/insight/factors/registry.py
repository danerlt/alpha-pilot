"""Factor registry (spec §5.2).

`FactorContext` and the `Factor` Protocol live in `context.py` to keep this
module free of downward imports — otherwise the catalog modules (which
import FactorContext) would circularly re-enter the registry.
"""
from __future__ import annotations

from src.services.insight.factors.context import Factor, FactorContext

# Re-export so older imports `from src.services.insight.factors.registry import FactorContext`
# keep working.
__all__ = ["Factor", "FactorContext", "FactorRegistry", "DEFAULT_REGISTRY"]


class FactorRegistry:
    """Canonical list of active factors for V0.1."""

    def __init__(self):
        self._factors: dict[str, Factor] = {}

    def register(self, factor: Factor) -> None:
        """Register or replace a factor by name (last-write-wins)."""
        self._factors[factor.name] = factor

    def unregister(self, name: str) -> None:
        self._factors.pop(name, None)

    def get(self, name: str) -> Factor | None:
        return self._factors.get(name)

    def all_active(self) -> list[Factor]:
        """Return factors in deterministic (name-sorted) order so
        FactorComputer produces stable JSON output."""
        return [self._factors[k] for k in sorted(self._factors)]

    def names(self) -> list[str]:
        return sorted(self._factors)


# Default registry — populated at import time.
DEFAULT_REGISTRY = FactorRegistry()


def _install_defaults() -> None:
    """Import catalog modules and register the six V0.1 presets."""
    from src.services.insight.factors.catalog import (
        breakout_validity,
        momentum_quality,
        pullback_opportunity,
        trend_strength,
        volatility_regime,
        volume_confirmation,
    )

    DEFAULT_REGISTRY.register(trend_strength.TrendStrength())
    DEFAULT_REGISTRY.register(momentum_quality.MomentumQuality())
    DEFAULT_REGISTRY.register(volume_confirmation.VolumeConfirmation())
    DEFAULT_REGISTRY.register(volatility_regime.VolatilityRegime())
    DEFAULT_REGISTRY.register(breakout_validity.BreakoutValidity())
    DEFAULT_REGISTRY.register(pullback_opportunity.PullbackOpportunity())


_install_defaults()
