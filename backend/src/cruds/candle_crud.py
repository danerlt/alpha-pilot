"""CRUD for src.models.candle."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.candle import Candle


class CandleCrud(BaseCrud[Candle]):
    model = Candle

    def find_latest(
        self,
        session: Session,
        *,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        """最近 limit 根 K 线, 按 open_time 正序返回。"""
        rows = list(session.execute(
            select(Candle).where(
                Candle.account_id == account_id,
                Candle.trading_mode == trading_mode,
                Candle.symbol == symbol,
                Candle.timeframe == timeframe,
            ).order_by(Candle.open_time.desc()).limit(limit)
        ).scalars())
        return list(reversed(rows))

candle_crud = CandleCrud()
