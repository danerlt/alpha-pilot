"""实验室 scanner — 影子执行/评估/灰度回滚 (handoff 3.5)。

与策略循环同频; 无 SHADOW/CANARY 候选时开销近似为零。
"""
from __future__ import annotations

import logging

logger = logging.getLogger("scheduler.lab")


def lab_job() -> None:
    from src.configs.app_configs import get_settings
    from src.controllers.dependencies import get_adapter
    from src.db.session import get_db_session
    from src.services.events.outbox import OutboxWriter
    from src.services.lab.shadow_runner import ShadowRunner

    settings = get_settings()
    mode = settings.TRADING_MODE
    trading_mode = mode.value if hasattr(mode, "value") else mode
    try:
        with get_db_session() as session:
            stats = ShadowRunner(
                session, get_adapter(), outbox=OutboxWriter(),
            ).run_once(trading_mode=trading_mode)
        if any(stats.values()):
            logger.info("lab_job done: %s", stats)
    except Exception:
        logger.exception("lab_job failed")
