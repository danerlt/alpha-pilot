"""StrategyScorer — 按维度对窗口内交易聚合评分并 upsert (PRD 8.2.5)。

score_window():
  1. 查 trading_mode 隔离下、closed_at 在窗口内的已平仓交易
  2. 按 (strategy_mode, symbol, regime) 分组 (None 维度用占位 'unknown')
  3. 每组 compute_strategy_metrics → upsert StrategyScore (字段映射见下)
  4. 返回 upsert 的分组数

字段映射: metrics → strategy_scores 表
  total_pnl → pnl_sum / total_trades → sample_count
  stop_loss_exit_rate → false_breakout_rate (breakout 维度下止损退出 = 假突破)
  regime_fit_score 暂留 None (需 regime 对照基线, 留 V0.3)
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.strategy_score_crud import strategy_score_crud
from src.models.trade import Trade
from src.services.insight.scoring.metrics import compute_strategy_metrics

logger = logging.getLogger(__name__)

_UNKNOWN = "unknown"


class StrategyScorer:
    def __init__(self, session: Session, account_id: int = 1):
        self._session = session
        self._account_id = account_id

    def score_window(self, *, trading_mode: str, window: str = "30d", window_days: int = 30) -> int:
        """评分一个时间窗; 返回 upsert 的分组数 (不 commit, 由调用方 commit)。"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        trades = list(
            self._session.execute(
                select(Trade).where(
                    Trade.trading_mode == trading_mode,
                    Trade.closed_at >= cutoff,
                )
            ).scalars()
        )

        groups: dict[tuple[str, str, str], list[Trade]] = defaultdict(list)
        for t in trades:
            key = (t.strategy_mode or _UNKNOWN, t.symbol, t.regime or _UNKNOWN)
            groups[key].append(t)

        for (strategy_mode, symbol, regime), group_trades in groups.items():
            m = compute_strategy_metrics(group_trades)
            strategy_score_crud.upsert_score(
                self._session,
                account_id=self._account_id,
                strategy_mode=strategy_mode, symbol=symbol, regime=regime, window=window,
                win_rate=m.win_rate,
                pnl_sum=m.total_pnl,
                max_drawdown=m.max_drawdown,
                sharpe=m.sharpe,
                false_breakout_rate=m.stop_loss_exit_rate,
                regime_fit_score=None,
                sample_count=m.total_trades,
            )

        logger.info(
            "StrategyScorer scored window=%s mode=%s groups=%d trades=%d",
            window, trading_mode, len(groups), len(trades),
        )
        return len(groups)
