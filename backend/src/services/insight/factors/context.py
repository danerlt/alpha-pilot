"""FactorContext + Factor Protocol, isolated from the registry to avoid
circular imports between the catalog modules (which import the context)
and the registry (which imports the catalog to install defaults).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from src.services.insight.indicators.computer import IndicatorValues


@dataclass
class FactorContext:
    """Everything a factor can see when computing its value.

    `candles` is ordered time-forward (oldest first). `indicators` holds the
    pre-computed indicator snapshot for the latest bar so factors don't
    re-run pandas-ta themselves.
    """
    candles: pd.DataFrame
    indicators: IndicatorValues


class Factor(Protocol):
    """A named, versioned signal producer. Protocol makes duck-typing explicit."""
    name: str
    version: int

    def compute(self, ctx: FactorContext) -> float: ...
