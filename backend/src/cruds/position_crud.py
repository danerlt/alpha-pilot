"""CRUD for src.models.position."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.enums import PositionStatus
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

    def find_open_symbols(
        self, session: Session, *, trading_mode: str, account_id: int = 1,
    ) -> set[str]:
        """当前 OPEN 持仓的 symbol 集合。"""
        rows = session.execute(
            select(Position.symbol).where(
                Position.account_id == account_id,
                Position.trading_mode == trading_mode,
                Position.status == PositionStatus.OPEN.value,
            ).distinct()
        ).scalars()
        return set(rows)

position_crud = PositionCrud()
