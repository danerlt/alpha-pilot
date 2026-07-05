"""CRUD for src.models.account."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.account import AccountSnapshot


class AccountSnapshotCrud(BaseCrud[AccountSnapshot]):
    model = AccountSnapshot

    def find_latest(
        self, session: Session, *, trading_mode: str, account_id: int = 1,
    ) -> AccountSnapshot | None:
        return session.execute(
            select(AccountSnapshot).where(
                AccountSnapshot.account_id == account_id,
                AccountSnapshot.trading_mode == trading_mode,
            ).order_by(AccountSnapshot.snapshot_at.desc()).limit(1)
        ).scalars().first()

    def find_series(
        self, session: Session, *, trading_mode: str, limit: int, account_id: int = 1,
    ) -> list[AccountSnapshot]:
        """最近 limit 个快照, 按时间正序 (权益曲线)。"""
        rows = list(session.execute(
            select(AccountSnapshot).where(
                AccountSnapshot.account_id == account_id,
                AccountSnapshot.trading_mode == trading_mode,
            ).order_by(AccountSnapshot.snapshot_at.desc()).limit(limit)
        ).scalars())
        return list(reversed(rows))

account_snapshot_crud = AccountSnapshotCrud()
