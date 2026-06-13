"""CRUD for src.models.account."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.account import AccountSnapshot


class AccountSnapshotCrud(BaseCrud[AccountSnapshot]):
    model = AccountSnapshot

account_snapshot_crud = AccountSnapshotCrud()
