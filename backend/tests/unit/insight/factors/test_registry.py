"""Tests for FactorRegistry."""
from __future__ import annotations

import pandas as pd

from src.services.insight.factors.registry import (
    DEFAULT_REGISTRY,
    FactorContext,
    FactorRegistry,
)
from src.services.insight.indicators.computer import IndicatorValues


class _FakeFactor:
    name = "fake"
    version = 1
    def compute(self, ctx: FactorContext) -> float:
        return 0.5


def test_register_and_get():
    reg = FactorRegistry()
    reg.register(_FakeFactor())
    f = reg.get("fake")
    assert f is not None
    assert f.name == "fake"
    assert f.version == 1


def test_register_replaces_same_name_last_write_wins():
    reg = FactorRegistry()

    class A: name = "x"; version = 1
    class B: name = "x"; version = 2

    reg.register(A())
    reg.register(B())
    assert reg.get("x").version == 2


def test_unregister():
    reg = FactorRegistry()
    reg.register(_FakeFactor())
    reg.unregister("fake")
    assert reg.get("fake") is None


def test_all_active_returns_sorted_by_name():
    reg = FactorRegistry()

    class A: name = "zebra"; version = 1
    class B: name = "alpha"; version = 1

    reg.register(A())
    reg.register(B())
    names = [f.name for f in reg.all_active()]
    assert names == ["alpha", "zebra"]


def test_default_registry_has_six_presets():
    """The six V0.1 factors must all be wired up."""
    expected = {
        "trend_strength",
        "momentum_quality",
        "volume_confirmation",
        "volatility_regime",
        "breakout_validity",
        "pullback_opportunity",
    }
    assert set(DEFAULT_REGISTRY.names()) == expected


def test_default_registry_returns_floats_on_empty_context():
    """Every factor must handle an empty/degenerate context without raising."""
    ctx = FactorContext(
        candles=pd.DataFrame(columns=["open", "high", "low", "close", "volume"]),
        indicators=IndicatorValues(),
    )
    for factor in DEFAULT_REGISTRY.all_active():
        value = factor.compute(ctx)
        assert isinstance(value, float), f"{factor.name} must return float"
