"""CRUD for src.models.regime."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.regime import RegimeSnapshot


class RegimeSnapshotCrud(BaseCrud[RegimeSnapshot]):
    model = RegimeSnapshot

    def find_latest_by_symbol(
        self, session: Session, *, trading_mode: str, symbol: str, account_id: int = 1,
    ) -> RegimeSnapshot | None:
        return session.execute(
            select(RegimeSnapshot).where(
                RegimeSnapshot.account_id == account_id,
                RegimeSnapshot.trading_mode == trading_mode,
                RegimeSnapshot.symbol == symbol,
            ).order_by(RegimeSnapshot.snapshot_at.desc()).limit(1)
        ).scalars().first()

regime_snapshot_crud = RegimeSnapshotCrud()
