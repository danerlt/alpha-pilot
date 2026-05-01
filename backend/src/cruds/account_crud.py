"""CRUD for src.models.account."""
from __future__ import annotations

from src.models.account import AccountSnapshot
from src.cruds.base_crud import BaseCrud


class AccountSnapshotCrud(BaseCrud[AccountSnapshot]):
    model = AccountSnapshot

account_snapshot_crud = AccountSnapshotCrud()
