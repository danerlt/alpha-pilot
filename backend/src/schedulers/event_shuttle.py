"""EventShuttle daemon — outbox → Redis Pub/Sub 推送（spec §4.8.2）。

scheduler 容器内独立 daemon thread 运行；不与 APScheduler 共享调度，纯 while 循环。
保持与原 ``src/workers/event_shuttle.py::EventShuttle`` 的行为一致；区别是
改由 scheduler 进程的 daemon thread 启动。
"""
from __future__ import annotations

import logging
import threading

from src.configs import get_app_config
from src.db.engines import get_engine

logger = logging.getLogger("scheduler.event_shuttle")


def event_shuttle_loop(stop_flag: threading.Event) -> None:
    """daemon thread 入口：按配置间隔轮询 outbox 推送。

    出错时短退避不退出，进程退出时由 daemon=True 自动结束。
    """
    from src.services.event_bus import RedisStreamsBus
    from src.workers.event_shuttle import EventShuttle

    cfg = get_app_config()
    engine = get_engine()
    bus = RedisStreamsBus(redis_url=cfg.REDIS_URL)
    shuttle = EventShuttle(
        engine=engine,
        bus=bus,
        max_failed_attempts=cfg.EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS,
    )

    idle_sleep = cfg.EVENT_SHUTTLE_IDLE_SLEEP_SECONDS
    batch_size = cfg.EVENT_SHUTTLE_BATCH_SIZE
    logger.info(
        "EventShuttle daemon started; idle_sleep=%.2fs batch=%d",
        idle_sleep, batch_size,
    )

    while not stop_flag.is_set():
        try:
            published = shuttle.drain_once(batch_size=batch_size)
            if published == 0:
                stop_flag.wait(idle_sleep)
        except Exception:
            logger.exception("event_shuttle loop unhandled error")
            stop_flag.wait(1.0)

    logger.info("EventShuttle daemon stopping")
