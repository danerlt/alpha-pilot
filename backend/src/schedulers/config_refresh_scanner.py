"""Config refresh scanner — APScheduler 周期触发 DB 配置兜底刷新（ADR-0001 P1）。

每 ``CONFIG_REFRESH_INTERVAL_SECONDS`` 触发一次，从 DB 重载 runtime 配置到进程内单例，
把前端设置页改的配置在 scheduler 进程的生效延迟从 ≤策略周期(15min) 压到 ~10s。
"""
from __future__ import annotations

import logging

logger = logging.getLogger("scheduler.config_refresh")


def config_refresh_job() -> None:
    """从 DB 兜底刷新 runtime 配置（容错，DB 异常只 warning）。"""
    from src.services.system.runtime_config import refresh_runtime_settings_safe

    refresh_runtime_settings_safe(source="periodic")
