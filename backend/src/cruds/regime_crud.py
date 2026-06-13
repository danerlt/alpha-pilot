"""CRUD for src.models.regime."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.regime import RegimeSnapshot


class RegimeSnapshotCrud(BaseCrud[RegimeSnapshot]):
    model = RegimeSnapshot

regime_snapshot_crud = RegimeSnapshotCrud()
