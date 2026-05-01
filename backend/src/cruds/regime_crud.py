"""CRUD for src.models.regime."""
from __future__ import annotations

from src.models.regime import RegimeSnapshot
from src.cruds.base_crud import BaseCrud


class RegimeSnapshotCrud(BaseCrud[RegimeSnapshot]):
    model = RegimeSnapshot

regime_snapshot_crud = RegimeSnapshotCrud()
