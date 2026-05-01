"""CRUD for src.models.position."""
from __future__ import annotations

from src.models.position import Position
from src.cruds.base_crud import BaseCrud


class PositionCrud(BaseCrud[Position]):
    model = Position

position_crud = PositionCrud()
