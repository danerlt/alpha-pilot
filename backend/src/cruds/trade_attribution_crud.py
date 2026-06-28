"""CRUD for src.models.attribution.TradeAttribution (PRD 8.1.3 逐笔归因)。

upsert_for_trade: 按 trade_id 幂等写入 (重跑归因更新而非插重复行)。
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.attribution import TradeAttribution


class TradeAttributionCrud(BaseCrud[TradeAttribution]):
    model = TradeAttribution

    def find_by_trade(self, session: Session, trade_id: int) -> TradeAttribution | None:
        return session.execute(
            select(TradeAttribution).where(TradeAttribution.trade_id == trade_id)
        ).scalar_one_or_none()

    def upsert_for_trade(
        self, session: Session, *,
        trade_id: int, by_symbol: dict | None, by_time_bucket: str | None,
        by_exit_reason: str | None, narrative: str,
    ) -> TradeAttribution:
        """按 trade_id upsert; 不 commit。"""
        obj = self.find_by_trade(session, trade_id)
        if obj is None:
            obj = TradeAttribution(trade_id=trade_id)
            session.add(obj)
        obj.by_symbol = by_symbol
        obj.by_time_bucket = by_time_bucket
        obj.by_exit_reason = by_exit_reason
        obj.narrative = narrative
        obj.generated_at = datetime.now(timezone.utc)
        session.flush()
        return obj

    def list_recent(self, session: Session, limit: int = 50) -> list[TradeAttribution]:
        return list(
            session.execute(
                select(TradeAttribution)
                .order_by(TradeAttribution.trade_id.desc())
                .limit(limit)
            ).scalars()
        )


trade_attribution_crud = TradeAttributionCrud()
