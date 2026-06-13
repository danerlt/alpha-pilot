"""CRUD for src.models.position."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.position import Position


class PositionCrud(BaseCrud[Position]):
    model = Position

position_crud = PositionCrud()
