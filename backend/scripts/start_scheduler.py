"""Scheduler 进程入口（spec §4.8）。

单容器运行：APScheduler 后台线程跑定时 job + 主线程 BRPOP 异步任务队列。
EventShuttle daemon thread 独立运行 outbox → Redis Pub/Sub。

graceful shutdown：SIGTERM → stop_flag.set() → 主循环退出 → APScheduler.shutdown(wait=True)
+ EventShuttle daemon join(timeout=5)；docker stop_grace_period: 60s 兜底。
"""
from __future__ import annotations

import logging
import signal
import threading

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from src.configs import get_app_config
from src.utils.log import init_logger

# 必须在最早 init logger
init_logger("scheduler")

logger = logging.getLogger("scheduler")
_stop_flag = threading.Event()


def _setup_scheduler() -> BackgroundScheduler:
    """启动 APScheduler 后台线程，注册定时 job。"""
    cfg = get_app_config()
    scheduler = BackgroundScheduler(
        jobstores={
            "default": SQLAlchemyJobStore(
                url=cfg.db_uri,
                tablename=cfg.APSCHEDULER_JOBS_TABLE,
            ),
        },
        job_defaults={
            "coalesce": True,
            "misfire_grace_time": 60,
            "max_instances": 1,  # 同一 job 不并发（避免策略循环重叠）
        },
    )

    from src.schedulers.position_monitor_scanner import position_monitor_job
    from src.schedulers.strategy_pipeline_scanner import strategy_pipeline_job

    scheduler.add_job(
        strategy_pipeline_job, "interval",
        minutes=cfg.STRATEGY_LOOP_INTERVAL_MINUTES,
        id="strategy_loop", replace_existing=True,
    )
    scheduler.add_job(
        position_monitor_job, "interval",
        seconds=cfg.POSITION_MONITOR_INTERVAL_SECONDS,
        id="position_monitor", replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "APScheduler started: strategy_loop=%dm position_monitor=%ds (PG JobStore: %s)",
        cfg.STRATEGY_LOOP_INTERVAL_MINUTES,
        cfg.POSITION_MONITOR_INTERVAL_SECONDS,
        cfg.APSCHEDULER_JOBS_TABLE,
    )
    return scheduler


def _start_event_shuttle() -> threading.Thread:
    """启动 EventShuttle daemon thread（outbox → Redis Pub/Sub）。"""
    from src.schedulers.event_shuttle import event_shuttle_loop

    t = threading.Thread(
        target=event_shuttle_loop,
        args=(_stop_flag,),
        name="event-shuttle",
        daemon=True,
    )
    t.start()
    logger.info("EventShuttle daemon thread started")
    return t


def _consume_task_queue() -> None:
    """主线程阻塞消费 Redis 异步任务队列（task_requests 表 + alphapilot:tasks 队列）。

    spec §4.9.1: scheduler 启动时先 recover_orphans, 然后 BRPOP 消费循环。
    """
    cfg = get_app_config()
    from src.db.session import get_db_session
    from src.services.task_dispatcher import TaskDispatcher
    from src.utils.redis import get_redis_client

    dispatcher = TaskDispatcher(
        db_factory=get_db_session,
        redis_client=get_redis_client(),
        queue_key=cfg.TASK_QUEUE_KEY,
    )
    try:
        recovered = dispatcher.recover_orphans()
        logger.info("recover_orphans done: recovered=%d", recovered)
    except Exception:
        logger.exception("recover_orphans failed (continuing)")
    dispatcher.dispatch_loop(_stop_flag)


def _install_signal_handlers() -> None:
    def _on_signal(*_args):
        logger.info("Received signal, exiting gracefully...")
        _stop_flag.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)


def main() -> None:
    """scheduler 容器入口。"""
    _install_signal_handlers()

    scheduler = _setup_scheduler()
    shuttle = _start_event_shuttle()

    try:
        _consume_task_queue()  # 主线程阻塞
    finally:
        # SIGTERM 后：
        # 1. 主循环退出（不再取新任务）
        # 2. APScheduler shutdown(wait=True): 等待运行中 job 完成（避免策略循环半完成）
        # 3. EventShuttle daemon: daemon=True 自然 kill；join(timeout=5) 给优雅窗口
        # 60s docker stop_grace_period 内完成；超时 SIGKILL，下次 recover_orphan_tasks 兜底
        scheduler.shutdown(wait=True)
        shuttle.join(timeout=5)
        logger.info("Scheduler container exiting")


if __name__ == "__main__":
    main()
