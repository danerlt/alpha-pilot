"""策略评分 scanner — APScheduler 周期触发 (PRD 8.2.5)。

对当前 trading_mode 最近 N 天的已平仓交易按维度评分, upsert strategy_scores。
低频任务 (默认每日), 对历史已平仓交易聚合, 不影响实时交易链路。
"""
from __future__ import annotations

import logging

logger = logging.getLogger("scheduler.strategy_scoring")


def strategy_scoring_job() -> None:
    from src.configs.app_configs import get_settings
    from src.db.session import get_db_session
    from src.services.insight.scoring.scorer import StrategyScorer

    settings = get_settings()
    try:
        with get_db_session() as session:
            n = StrategyScorer(session).score_window(
                trading_mode=settings.TRADING_MODE.value, window="30d", window_days=30,
            )
            session.commit()
        logger.info("strategy_scoring_job done: groups=%d", n)
    except Exception:
        logger.exception("strategy_scoring_job failed")
