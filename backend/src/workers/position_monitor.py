"""持仓监控 Worker — 每 10 秒执行一次，检查止损/止盈/熔断。"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis as redis_lib
from sqlalchemy.orm import Session

from src.services.execution.account_state_service import get_daily_pnl
from src.services.execution.monitoring_service import run_monitor_cycle
from src.shared.config import get_settings

logger = logging.getLogger(__name__)


def _get_redis() -> redis_lib.Redis:
    settings = get_settings()
    return redis_lib.from_url(settings.REDIS_URL, decode_responses=True)


def _publish(r: redis_lib.Redis, channel: str, data: dict[str, Any]) -> None:
    try:
        r.publish(channel, json.dumps(data))
    except Exception as e:
        logger.error("Redis publish failed on channel %s: %s", channel, e)


def run_position_monitor(db: Session) -> None:
    """执行一次持仓监控循环（由 APScheduler 定期调用）。"""
    r = _get_redis()

    try:
        _, daily_pnl_pct = get_daily_pnl(db)
        result = run_monitor_cycle(db, daily_pnl_pct)

        if result["stop_loss_closed"]:
            _publish(r, "trading_events", {
                "type": "stop_loss_triggered",
                "position_ids": result["stop_loss_closed"],
            })

        if result["take_profit_closed"]:
            _publish(r, "trading_events", {
                "type": "take_profit_triggered",
                "position_ids": result["take_profit_closed"],
            })

        if result["circuit_breaker_triggered"]:
            _publish(r, "trading_events", {
                "type": "circuit_breaker",
                "reason": "daily_loss_limit",
            })

    except Exception as e:
        logger.error("Position monitor cycle failed: %s", e)
