"""CRUD for src.models.trade."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.trade import Trade


class TradeCrud(BaseCrud[Trade]):
    model = Trade

trade_crud = TradeCrud()
