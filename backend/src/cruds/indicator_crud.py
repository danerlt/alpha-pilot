"""CRUD for src.models.indicator."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.indicator import IndicatorSnapshot


class IndicatorSnapshotCrud(BaseCrud[IndicatorSnapshot]):
    model = IndicatorSnapshot

    def find_latest_by_symbol(
        self, session: Session, *, trading_mode: str, symbol: str, account_id: int = 1,
    ) -> IndicatorSnapshot | None:
        return session.execute(
            select(IndicatorSnapshot).where(
                IndicatorSnapshot.account_id == account_id,
                IndicatorSnapshot.trading_mode == trading_mode,
                IndicatorSnapshot.symbol == symbol,
            ).order_by(IndicatorSnapshot.snapshot_at.desc()).limit(1)
        ).scalars().first()

indicator_snapshot_crud = IndicatorSnapshotCrud()
