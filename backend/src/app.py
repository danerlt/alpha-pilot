"""FastAPI 应用入口 — ``src/app.py``（模板规范的"src 内唯一启动文件"）。

``from src.app import app`` 即可获取 FastAPI 实例。
原 ``src/app/`` 包改名为 ``src/api/``，避免与本文件命名冲突。

阶段 1 内容：
- 中间件栈注入（CorrelationId / RequestLogging / ErrorLogging）
- 注册全局 exception handler（兼容现有 HTTPException 行为）
- 复用现有 routers (``src/api/routers/*``) 与 lifespan、admin_bootstrap
- 响应体格式 / 异常处理保持当前行为（不切 Response[T]）

阶段 4 / 5 会再次重构（路由迁到 controllers/、移除 lifespan 内 scheduler）。
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import router as _root_router
from src.api.routers.commands import router as _commands_router
from src.api.routers.events_catchup import router as _events_catchup_router
from src.api.websocket import redis_subscriber, websocket_endpoint
from src.common.exception.exception_handler import register_exception_handlers
from src.configs import get_app_config
from src.control.kill_switch.service import KillSwitchService
from src.db.session import get_db_session
from src.middleware.error_logging_middleware import ErrorLoggingMiddleware
from src.middleware.request_logging_middleware import RequestLoggingMiddleware
from src.services.admin_bootstrap import ensure_default_admin
from src.utils.log import init_logger
from src.utils.uuid import get_uuid_without_hyphen

# 初始化日志（必须在最早）
init_logger("api")

logger = logging.getLogger("app")

_scheduler: BackgroundScheduler | None = None


def _strategy_job() -> None:
    from src.workers.strategy_loop import run_strategy_loop

    with get_db_session() as db:
        try:
            if KillSwitchService(db).is_paused():
                logger.info("kill_switch=paused; strategy_loop skipped")
                return
            run_strategy_loop(db)
        except Exception as e:
            logger.error("Strategy loop error: %s", e)


def _monitor_job() -> None:
    from src.workers.position_monitor import run_position_monitor

    with get_db_session() as db:
        try:
            if KillSwitchService(db).is_paused():
                logger.debug("kill_switch=paused; position_monitor running (monitor-only)")
            run_position_monitor(db)
        except Exception as e:
            logger.error("Position monitor error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    settings = get_app_config()

    with get_db_session() as db:
        ensure_default_admin(db, settings)

    _scheduler = BackgroundScheduler()
    if getattr(settings, "USE_NEW_PIPELINE_WORKER", False):
        from src.workers.scheduler_jobs import (
            new_position_monitor_job,
            new_strategy_pipeline_job,
        )
        _scheduler.add_job(
            new_strategy_pipeline_job, "interval",
            minutes=settings.STRATEGY_LOOP_INTERVAL_MINUTES, id="strategy_loop",
        )
        _scheduler.add_job(
            new_position_monitor_job, "interval",
            seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS, id="position_monitor",
        )
        logger.info("Scheduler using NEW pipeline worker")
    else:
        _scheduler.add_job(
            _strategy_job, "interval",
            minutes=settings.STRATEGY_LOOP_INTERVAL_MINUTES, id="strategy_loop",
        )
        _scheduler.add_job(
            _monitor_job, "interval",
            seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS, id="position_monitor",
        )
        logger.info("Scheduler using LEGACY services/* worker")
    _scheduler.start()
    logger.info(
        "interval: strategy_loop=%dm, position_monitor=%ds",
        settings.STRATEGY_LOOP_INTERVAL_MINUTES,
        settings.POSITION_MONITOR_INTERVAL_SECONDS,
    )

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


def _docs_enabled() -> bool:
    """testnet 默认开 docs，mainnet 默认关。可被 ALPHAPILOT_FORCE_DOCS=1 强开。"""
    if os.getenv("ALPHAPILOT_FORCE_DOCS") == "1":
        return True
    settings = get_app_config()
    mode = settings.TRADING_MODE.value if hasattr(settings.TRADING_MODE, "value") else settings.TRADING_MODE
    return mode != "mainnet"


def create_app() -> FastAPI:
    settings = get_app_config()
    docs_on = _docs_enabled()

    app = FastAPI(
        title="AlphaPilot API",
        description="AI Autonomous Trading System",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_on else None,
        redoc_url="/redoc" if docs_on else None,
        openapi_url="/openapi.json" if docs_on else None,
    )

    # ── 全局 exception handler（注册以便阶段 4 切 Response[T] 时直接生效）─
    register_exception_handlers(app)

    # ── 中间件（注册顺序从内到外）────────────────────────────────────────
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    if settings.ENABLE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        )
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
        generator=get_uuid_without_hyphen,
        update_request_header=True,
    )

    # ── 路由（沿用现有 routers，阶段 4 重组到 controllers/）────────────────
    app.include_router(_root_router)
    app.include_router(_commands_router)
    app.include_router(_events_catchup_router)
    app.add_api_websocket_route("/ws", websocket_endpoint)

    return app


app = create_app()


__all__ = ["app", "create_app", "lifespan"]
