"""Strategy 循环 scanner — APScheduler 周期触发。"""
from __future__ import annotations

import logging

from src.db.session import get_db_session
from src.services.risk.kill_switch import KillSwitchService

logger = logging.getLogger("scheduler.strategy_pipeline")


def strategy_pipeline_job() -> None:
    """每 ``STRATEGY_LOOP_INTERVAL_MINUTES`` 触发一次。

    保持与原 ``src/app.py::_strategy_job`` 的行为一致；区别是改由 scheduler 进程触发。
    """
    from src.workers.strategy_loop import run_strategy_loop

    with get_db_session() as db:
        try:
            if KillSwitchService(db).is_paused():
                logger.info("kill_switch=paused; strategy_loop skipped")
                return
            run_strategy_loop(db)
        except Exception as e:
            logger.error("Strategy loop error: %s", e)
