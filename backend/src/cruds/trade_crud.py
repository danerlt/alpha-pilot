"""CRUD for src.models.trade."""
from __future__ import annotations

from src.models.trade import Trade
from src.cruds.base_crud import BaseCrud


class TradeCrud(BaseCrud[Trade]):
    model = Trade

trade_crud = TradeCrud()
