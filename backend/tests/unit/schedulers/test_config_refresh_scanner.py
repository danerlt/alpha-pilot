"""P1 周期兜底刷新：config_refresh_job（scheduler）+ API 后台刷新 loop + 配置项。

DB 配置变更实时下发 P1：各进程每 ~CONFIG_REFRESH_INTERVAL_SECONDS 兜底刷一次，
把 scheduler 侧 ≤策略周期(15min) 的延迟压到 ~10s。
"""
import asyncio
from unittest.mock import patch

from src.configs.app_configs import SchedulerConfig


def test_config_refresh_interval_default_is_10s():
    assert SchedulerConfig.model_fields["CONFIG_REFRESH_INTERVAL_SECONDS"].default == 10


def test_config_refresh_job_refreshes_with_periodic_source():
    with patch("src.services.system.runtime_config.refresh_runtime_settings_safe") as m:
        from src.schedulers.config_refresh_scanner import config_refresh_job

        config_refresh_job()
    m.assert_called_once_with(source="periodic")


async def test_api_periodic_config_refresh_calls_refresh():
    with patch("src.services.system.runtime_config.refresh_runtime_settings_safe") as m:
        from src.app import _periodic_config_refresh

        task = asyncio.create_task(_periodic_config_refresh(0.01))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    assert m.call_count >= 1
    m.assert_called_with(source="api_periodic")
