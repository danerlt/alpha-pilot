"""CRUD for src.models.attribution.StrategyScore (PRD 8.2.5 策略评分)。

upsert_score: 按 unique key (account_id, strategy_mode, symbol, regime, window) 幂等写入——
同维度+窗口重复评分更新而非插重复行。
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.attribution import StrategyScore


class StrategyScoreCrud(BaseCrud[StrategyScore]):
    model = StrategyScore

    def find_one(
        self, session: Session, *,
        account_id: int, strategy_mode: str, symbol: str, regime: str, window: str,
    ) -> StrategyScore | None:
        return session.execute(
            select(StrategyScore).where(
                StrategyScore.account_id == account_id,
                StrategyScore.strategy_mode == strategy_mode,
                StrategyScore.symbol == symbol,
                StrategyScore.regime == regime,
                StrategyScore.window == window,
            )
        ).scalar_one_or_none()

    def upsert_score(
        self, session: Session, *,
        account_id: int, strategy_mode: str, symbol: str, regime: str, window: str,
        win_rate: float | None, pnl_sum: float | None, max_drawdown: float | None,
        sharpe: float | None, false_breakout_rate: float | None,
        regime_fit_score: float | None, sample_count: int,
    ) -> StrategyScore:
        """按 unique key upsert; 不 commit (由 service 显式 commit)。"""
        obj = self.find_one(
            session, account_id=account_id, strategy_mode=strategy_mode,
            symbol=symbol, regime=regime, window=window,
        )
        if obj is None:
            obj = StrategyScore(
                account_id=account_id, strategy_mode=strategy_mode,
                symbol=symbol, regime=regime, window=window,
            )
            session.add(obj)
        obj.win_rate = win_rate
        obj.pnl_sum = pnl_sum
        obj.max_drawdown = max_drawdown
        obj.sharpe = sharpe
        obj.false_breakout_rate = false_breakout_rate
        obj.regime_fit_score = regime_fit_score
        obj.sample_count = sample_count
        session.flush()
        return obj

    def find_by_window(self, session: Session, *, account_id: int, window: str) -> list[StrategyScore]:
        return list(
            session.execute(
                select(StrategyScore)
                .where(StrategyScore.account_id == account_id, StrategyScore.window == window)
                .order_by(StrategyScore.sample_count.desc())
            ).scalars()
        )


strategy_score_crud = StrategyScoreCrud()
