"""position_monitor 包装层 — Plan 5 的 lifespan 由这里调度。

提供 run_position_monitor_once() 把 PositionMonitor.run_once 包装成
可由 APScheduler 或测试直接调用的入口; 注意区别于既有 services/...
里的旧 position_monitor.py (Plan 5 cleanup 时再合并)。
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.core.exchange.adapter import ExchangeAdapter
from src.services.events.outbox import OutboxWriter
from src.services.execution.account_state import AccountStateService
from src.services.execution.order_executor import OrderExecutor
from src.services.execution.position_monitor import MonitorResult, PositionMonitor

logger = logging.getLogger(__name__)


def run_position_monitor_once(
    *,
    db: Session,
    account_id: int,
    trading_mode: str,
    adapter: ExchangeAdapter,
    max_daily_loss_pct: float = 0.03,
    outbox: Optional[OutboxWriter] = None,
) -> MonitorResult:
    """组装服务并跑一次监控循环, 返回结果。"""
    executor = OrderExecutor(db, adapter, outbox=outbox)
    account = AccountStateService(db, adapter)
    monitor = PositionMonitor(db, adapter, executor, account, outbox=outbox)
    result = monitor.run_once(
        account_id=account_id, trading_mode=trading_mode,
        max_daily_loss_pct=max_daily_loss_pct,
    )
    db.commit()
    return result
