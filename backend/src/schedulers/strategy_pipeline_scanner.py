"""Strategy 循环 scanner — APScheduler 周期触发（V1 pipeline）。"""
from __future__ import annotations

import logging

logger = logging.getLogger("scheduler.strategy_pipeline")


def strategy_pipeline_job() -> None:
    """每 ``STRATEGY_LOOP_INTERVAL_MINUTES`` 触发一次。

    直接转发到 V1 ``new_strategy_pipeline_job``；KillSwitch 检查 + 风控 profile
    加载 + adapter/LLM 装配等都由 V1 job 自己处理。
    """
    from src.workers.scheduler_jobs import new_strategy_pipeline_job

    new_strategy_pipeline_job()
