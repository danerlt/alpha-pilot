"""CRUD for src.models.order."""
from __future__ import annotations

from src.models.order import Order
from src.cruds.base_crud import BaseCrud


class OrderCrud(BaseCrud[Order]):
    model = Order

order_crud = OrderCrud()
