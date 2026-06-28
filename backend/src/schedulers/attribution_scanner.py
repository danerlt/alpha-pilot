"""交易归因 scanner — APScheduler 周期触发 (PRD 8.1.3)。

对当前 trading_mode 最近 N 天已平仓交易逐笔归因 (写 trade_attributions)。
低频任务, 只读历史交易, 不影响实时交易链路。
"""
from __future__ import annotations

import logging

logger = logging.getLogger("scheduler.attribution")


def attribution_job() -> None:
    from src.configs.app_configs import get_settings
    from src.db.session import get_db_session
    from src.services.insight.attribution.service import AttributionService

    settings = get_settings()
    try:
        with get_db_session() as session:
            summary = AttributionService(session).attribute_window(
                trading_mode=settings.TRADING_MODE.value, window_days=30,
            )
            session.commit()
        logger.info("attribution_job done: trades=%d total_pnl=%.4f",
                    summary.total_trades, summary.total_pnl)
    except Exception:
        logger.exception("attribution_job failed")
