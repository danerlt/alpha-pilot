"""Position monitor scanner — APScheduler 周期触发（V1 pipeline）。"""
from __future__ import annotations

import logging

logger = logging.getLogger("scheduler.position_monitor")


def position_monitor_job() -> None:
    """每 ``POSITION_MONITOR_INTERVAL_SECONDS`` 触发一次。

    直接转发到 V1 ``new_position_monitor_job``；按 V1 设计，position monitor
    不接 KillSwitch，SL/TP 必须无条件运行保护已开仓位。
    """
    from src.workers.scheduler_jobs import new_position_monitor_job

    new_position_monitor_job()
