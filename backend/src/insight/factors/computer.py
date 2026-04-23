"""FactorComputer — compute every registered factor for the current bar,
UPSERT the resulting snapshot into factor_snapshots (spec §5.2).

The unique index `ix_factor_snapshots_unique(account_id, trading_mode,
symbol, timeframe, open_time)` means rerunning the same cycle produces
one stable row per bar. On SQLite (unit tests) we emulate UPSERT with
"delete then insert"; on Postgres the same `ON CONFLICT DO UPDATE` works
natively.
"""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.insight.factors.context import FactorContext
from src.insight.factors.registry import DEFAULT_REGISTRY, FactorRegistry
from src.insight.indicators.computer import IndicatorValues
from src.shared.models.factor import FactorSnapshot

logger = logging.getLogger(__name__)


class FactorComputer:
    def __init__(self, session: Session, registry: FactorRegistry = DEFAULT_REGISTRY):
        self._session = session
        self._registry = registry

    def compute_and_store(
        self,
        *,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        open_time: datetime,
        indicators: IndicatorValues,
        candles_df: pd.DataFrame,
    ) -> tuple[dict[str, float], int]:
        """Run every active factor; UPSERT the snapshot; return (factors_dict, snapshot_id)."""
        ctx = FactorContext(candles=candles_df, indicators=indicators)
        factors: dict[str, float] = {}
        versions: dict[str, int] = {}
        for factor in self._registry.all_active():
            try:
                factors[factor.name] = float(factor.compute(ctx))
                versions[factor.name] = factor.version
            except Exception:  # isolate one bad factor from the rest
                logger.exception("factor %s failed; substituting 0.0", factor.name)
                factors[factor.name] = 0.0
                versions[factor.name] = factor.version

        # Upsert: drop any pre-existing row for the same key then insert fresh.
        # The UNIQUE index guarantees at most one row per key; this works the
        # same on SQLite and Postgres without needing dialect-specific UPSERT.
        self._session.execute(
            delete(FactorSnapshot).where(
                FactorSnapshot.account_id == account_id,
                FactorSnapshot.trading_mode == trading_mode,
                FactorSnapshot.symbol == symbol,
                FactorSnapshot.timeframe == timeframe,
                FactorSnapshot.open_time == open_time,
            )
        )
        snap = FactorSnapshot(
            account_id=account_id,
            trading_mode=trading_mode,
            symbol=symbol,
            timeframe=timeframe,
            open_time=open_time,
            factors_json=factors,
            factor_def_versions_json=versions,
        )
        self._session.add(snap)
        self._session.flush()
        return factors, snap.id
