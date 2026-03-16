"""FastAPI 应用入口 — 注册路由和 APScheduler 调度器。"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from src.app.router import router
from src.shared.config import get_settings
from src.shared.db import get_session_factory

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _strategy_job() -> None:
    from src.workers.strategy_loop import run_strategy_loop
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
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
        run_position_monitor(db)
    except Exception as e:
        logger.error("Position monitor error: %s", e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    settings = get_settings()

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _strategy_job,
        "interval",
        minutes=settings.STRATEGY_LOOP_INTERVAL_MINUTES,
        id="strategy_loop",
    )
    _scheduler.add_job(
        _monitor_job,
        "interval",
        seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS,
        id="position_monitor",
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: strategy_loop every %dm, position_monitor every %ds",
        settings.STRATEGY_LOOP_INTERVAL_MINUTES,
        settings.POSITION_MONITOR_INTERVAL_SECONDS,
    )
    yield

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
