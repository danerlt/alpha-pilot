"""Position monitor scanner — APScheduler 周期触发。"""
from __future__ import annotations

import logging

from src.db.session import get_db_session
from src.services.risk.kill_switch import KillSwitchService

logger = logging.getLogger("scheduler.position_monitor")


def position_monitor_job() -> None:
    """每 ``POSITION_MONITOR_INTERVAL_SECONDS`` 触发一次。

    持仓监控允许在 kill_switch=paused 时继续刷新价格 + SL/TP（监控-only 模式），
    不允许主动开新仓（旧 worker 已实现这一约束）。
    """
    from src.workers.position_monitor import run_position_monitor

    with get_db_session() as db:
        try:
            if KillSwitchService(db).is_paused():
                logger.debug("kill_switch=paused; position_monitor running (monitor-only)")
            run_position_monitor(db)
        except Exception as e:
            logger.error("Position monitor error: %s", e)
