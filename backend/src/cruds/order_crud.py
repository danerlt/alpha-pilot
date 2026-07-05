"""CRUD for src.models.order."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.order import Order


class OrderCrud(BaseCrud[Order]):
    model = Order

    def find_latest(
        self, session: Session, *, trading_mode: str, limit: int, account_id: int = 1,
    ) -> list[Order]:
        return list(session.execute(
            select(Order).where(
                Order.account_id == account_id,
                Order.trading_mode == trading_mode,
            ).order_by(Order.id.desc()).limit(limit)
        ).scalars())

    def get_by_trace_id(self, session: Session, trace_id: str) -> Order | None:
        return session.execute(
            select(Order).where(Order.trace_id == trace_id)
        ).scalars().first()

    def find_by_decision_id(self, session: Session, decision_id: int) -> list[Order]:
        return list(session.execute(
            select(Order)
            .where(Order.ai_decision_id == decision_id)
            .order_by(Order.id)
        ).scalars())

order_crud = OrderCrud()
