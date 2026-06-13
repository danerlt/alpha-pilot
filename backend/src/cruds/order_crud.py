"""CRUD for src.models.order."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.order import Order


class OrderCrud(BaseCrud[Order]):
    model = Order

order_crud = OrderCrud()
