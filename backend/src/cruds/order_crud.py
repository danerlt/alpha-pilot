"""CRUD for src.models.order."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.order import Order


class OrderCrud(BaseCrud[Order]):
    model = Order

    def find_by_decision_id(self, session: Session, decision_id: int) -> list[Order]:
        return list(session.execute(
            select(Order)
            .where(Order.ai_decision_id == decision_id)
            .order_by(Order.id)
        ).scalars())

order_crud = OrderCrud()
