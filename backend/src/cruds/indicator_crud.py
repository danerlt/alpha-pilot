"""CRUD for src.models.indicator."""
from __future__ import annotations

from src.models.indicator import IndicatorSnapshot
from src.cruds.base_crud import BaseCrud


class IndicatorSnapshotCrud(BaseCrud[IndicatorSnapshot]):
    model = IndicatorSnapshot

indicator_snapshot_crud = IndicatorSnapshotCrud()
