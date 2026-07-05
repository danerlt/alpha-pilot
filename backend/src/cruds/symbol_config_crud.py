"""CRUD for src.models.symbol_config."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.symbol_config import SymbolConfig


class SymbolConfigCrud(BaseCrud[SymbolConfig]):
    model = SymbolConfig

    def find_enabled(self, session: Session) -> list[SymbolConfig]:
        """启用中的交易对, 按 sort_order/priority 排序。"""
        return list(session.execute(
            select(SymbolConfig)
            .where(SymbolConfig.enabled.is_(True))
            .order_by(SymbolConfig.sort_order, SymbolConfig.priority, SymbolConfig.id)
        ).scalars())

symbol_config_crud = SymbolConfigCrud()
