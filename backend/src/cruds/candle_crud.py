"""CRUD for src.models.candle."""
from __future__ import annotations

from src.models.candle import Candle
from src.cruds.base_crud import BaseCrud


class CandleCrud(BaseCrud[Candle]):
    model = Candle

candle_crud = CandleCrud()
