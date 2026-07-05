"""CRUD for src.models.position."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.position import Position


class PositionCrud(BaseCrud[Position]):
    model = Position

    def find_by_decision_id(self, session: Session, decision_id: int) -> list[Position]:
        return list(session.execute(
            select(Position)
            .where(Position.ai_decision_id == decision_id)
            .order_by(Position.id)
        ).scalars())

position_crud = PositionCrud()
