"""AttributionService — 逐笔归因 + 聚合拆解 (PRD 8.1.3 + 12.1)。

attribute_window():
  1. 查 trading_mode 隔离下、closed_at 在窗口内的已平仓交易
  2. 逐笔生成叙述 + 维度标签 → upsert trade_attributions
  3. 返回聚合 summary (按 symbol/exit_reason/regime/time_bucket 拆解盈亏)

只读历史交易, 零交易决策影响。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.trade_attribution_crud import trade_attribution_crud
from src.models.trade import Trade
from src.services.insight.attribution.calculator import (
    AttributionSummary,
    build_trade_narrative,
    compute_attribution_summary,
    time_bucket,
)

logger = logging.getLogger(__name__)


class AttributionService:
    def __init__(self, session: Session):
        self._session = session

    def _query_trades(self, trading_mode: str, window_days: int) -> list[Trade]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        return list(
            self._session.execute(
                select(Trade).where(
                    Trade.trading_mode == trading_mode,
                    Trade.closed_at >= cutoff,
                )
            ).scalars()
        )

    def attribute_window(self, *, trading_mode: str, window_days: int = 30) -> AttributionSummary:
        """逐笔归因写表 + 返回聚合 summary (不 commit, 由调用方 commit)。"""
        trades = self._query_trades(trading_mode, window_days)
        for t in trades:
            trade_attribution_crud.upsert_for_trade(
                self._session,
                trade_id=t.id,
                by_symbol={"symbol": t.symbol, "pnl": float(t.pnl)},
                by_time_bucket=time_bucket(t.closed_at),
                by_exit_reason=t.exit_reason,
                narrative=build_trade_narrative(t),
            )
        summary = compute_attribution_summary(trades)
        logger.info(
            "AttributionService attributed mode=%s trades=%d total_pnl=%.4f",
            trading_mode, summary.total_trades, summary.total_pnl,
        )
        return summary

    def summary_only(self, *, trading_mode: str, window_days: int = 30) -> AttributionSummary:
        """只算聚合拆解, 不写表 (REST summary 端点用)。"""
        return compute_attribution_summary(self._query_trades(trading_mode, window_days))
