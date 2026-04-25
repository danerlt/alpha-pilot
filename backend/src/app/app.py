"""FastAPI 应用入口 — 注册路由和 APScheduler 调度器。"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, WebSocket

from src.app.router import router
from src.app.routers.commands import router as commands_router
from src.app.routers.events_catchup import router as events_catchup_router
from src.app.websocket import redis_subscriber, websocket_endpoint
from src.control.kill_switch.service import KillSwitchService
from src.shared.config import get_base_settings, get_settings
from src.shared.db import get_session_factory
from src.shared.runtime_config import apply_runtime_settings_refresh
from src.services.admin_bootstrap import ensure_default_admin

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _strategy_job() -> None:
    from src.workers.strategy_loop import run_strategy_loop
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        if KillSwitchService(db).is_paused():
            logger.info("kill_switch=paused; strategy_loop skipped")
            return
        run_strategy_loop(db)
    except Exception as e:
        logger.error("Strategy loop error: %s", e)
    finally:
        db.close()


def _monitor_job() -> None:
    from src.workers.position_monitor import run_position_monitor
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        if KillSwitchService(db).is_paused():
            # 持仓监控允许在停机时继续刷新价格 + SL/TP, 不允许主动开新仓 (旧
            # worker 已经只做监控不开仓)。当前实现保持运行, 但加日志便于调试。
            logger.debug("kill_switch=paused; position_monitor running (monitor-only)")
        run_position_monitor(db)
    except Exception as e:
        logger.error("Position monitor error: %s", e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    base_settings = get_base_settings()
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        apply_runtime_settings_refresh(
            db,
            master_key=base_settings.APP_CONFIG_MASTER_KEY,
            default_trading_mode=base_settings.TRADING_MODE,
        )
        ensure_default_admin(db, base_settings)
    finally:
        db.close()

    settings = get_settings()

    _scheduler = BackgroundScheduler()
    if getattr(settings, "USE_NEW_PIPELINE_WORKER", False):
        from src.workers.scheduler_jobs import (
            new_position_monitor_job,
            new_strategy_pipeline_job,
        )
        _scheduler.add_job(
            new_strategy_pipeline_job, "interval",
            minutes=settings.STRATEGY_LOOP_INTERVAL_MINUTES,
            id="strategy_loop",
        )
        _scheduler.add_job(
            new_position_monitor_job, "interval",
            seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS,
            id="position_monitor",
        )
        logger.info("Scheduler using NEW pipeline worker (Plan 2/5)")
    else:
        _scheduler.add_job(
            _strategy_job, "interval",
            minutes=settings.STRATEGY_LOOP_INTERVAL_MINUTES,
            id="strategy_loop",
        )
        _scheduler.add_job(
            _monitor_job, "interval",
            seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS,
            id="position_monitor",
        )
        logger.info("Scheduler using LEGACY services/* worker")
    _scheduler.start()
    logger.info(
        "interval: strategy_loop=%dm, position_monitor=%ds",
        settings.STRATEGY_LOOP_INTERVAL_MINUTES,
        settings.POSITION_MONITOR_INTERVAL_SECONDS,
    )

    # 启动 Redis Pub/Sub → WebSocket 广播后台任务
    ws_task = asyncio.create_task(redis_subscriber(settings.REDIS_URL))
    logger.info("Redis subscriber task started")

    yield

    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


app = FastAPI(
    title="AlphaPilot API",
    description="AI Autonomous Trading System",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(commands_router)
app.include_router(events_catchup_router)
app.add_api_websocket_route("/ws", websocket_endpoint)
