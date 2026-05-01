"""TaskDispatcher — spec §4.9.1 前台 API 提任务 + scheduler 进程消费。

闭环:
  - enqueue: API 进程调用, 写 task_requests(PENDING) + LPUSH redis 队列
  - dispatch_loop: scheduler 进程主线程 BRPOP 消费, 路由到 handler
  - recover_orphans: scheduler 启动时把卡在 RUNNING 的标 FAILED (V0.1 不重新入队)
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Callable

from src.cruds.task_request_crud import task_request_crud

logger = logging.getLogger(__name__)

# Handler 注册表 (单进程内 dict)
HANDLERS: dict[str, Callable] = {}


def register_handler(task_type: str):
    """装饰器: 注册 handler(session, payload) -> None。"""
    def deco(fn: Callable):
        HANDLERS[task_type] = fn
        return fn
    return deco


class TaskDispatcher:
    def __init__(self, db_factory, redis_client, queue_key: str = "alphapilot:tasks"):
        """
        :param db_factory: 调用即返回新的 Session (例如 sessionmaker 或 lambda)。
        :param redis_client: redis-py 客户端 (需支持 lpush/brpop)。
        :param queue_key: Redis list key。
        """
        self._db_factory = db_factory
        self._redis = redis_client
        self._queue_key = queue_key

    # ── enqueue (API 端) ──────────────────────────────────────────────
    def enqueue(self, task_type: str, payload: dict, trading_mode: str = "testnet") -> int:
        """写 PENDING 行 + LPUSH redis, 返回 task_id。"""
        with self._db_factory() as session:
            obj = task_request_crud.create_pending(
                session, task_type=task_type, payload=payload, trading_mode=trading_mode,
            )
            task_id = obj.id
            session.commit()
        self._redis.lpush(self._queue_key, json.dumps({"task_id": task_id}))
        logger.info("Task enqueued: id=%s type=%s", task_id, task_type)
        return task_id

    # ── dispatch_loop (scheduler 端) ─────────────────────────────────
    def dispatch_loop(self, stop_flag: threading.Event) -> None:
        logger.info("TaskDispatcher loop started (queue=%s)", self._queue_key)
        while not stop_flag.is_set():
            try:
                item = self._redis.brpop(self._queue_key, timeout=1)
            except Exception as exc:
                logger.exception("BRPOP failed: %s", exc)
                continue
            if item is None:
                continue
            # redis-py 返 (key, value) 字节或字符串
            _, raw = item
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            try:
                data = json.loads(raw)
                task_id = int(data["task_id"])
            except (ValueError, KeyError, TypeError) as exc:
                logger.exception("Bad queue payload %r: %s", raw, exc)
                continue
            self._handle_one(task_id)

    def _handle_one(self, task_id: int) -> None:
        with self._db_factory() as session:
            running = task_request_crud.mark_running(session, task_id)
            if running is None:
                session.rollback()
                logger.warning("Task %s not in PENDING, skip", task_id)
                return
            task_type = running.task_type
            payload = running.payload or {}
            session.commit()

        handler = HANDLERS.get(task_type)
        if handler is None:
            with self._db_factory() as session:
                task_request_crud.mark_failed(
                    session, task_id, error_message=f"NoHandler:{task_type}",
                )
                session.commit()
            logger.error("No handler for task_type=%s (id=%s)", task_type, task_id)
            return

        try:
            with self._db_factory() as session:
                handler(session, payload)
                session.commit()
            with self._db_factory() as session:
                task_request_crud.mark_success(session, task_id)
                session.commit()
            logger.info("Task %s (%s) success", task_id, task_type)
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            logger.exception("Task %s (%s) failed: %s", task_id, task_type, err)
            try:
                with self._db_factory() as session:
                    task_request_crud.mark_failed(session, task_id, error_message=err)
                    session.commit()
            except Exception:
                logger.exception("mark_failed itself failed for task %s", task_id)

    # ── recover_orphans (scheduler 启动时) ───────────────────────────
    def recover_orphans(self, threshold_seconds: int = 300) -> int:
        """启动时把所有卡 RUNNING (started_at < now-threshold) 的标 FAILED。"""
        count = 0
        with self._db_factory() as session:
            orphans = task_request_crud.find_orphan_running(session, threshold_seconds)
            for obj in orphans:
                task_request_crud.mark_failed(
                    session, obj.id, error_message="orphaned (scheduler restart)",
                )
                count += 1
            session.commit()
        if count:
            logger.warning("Recovered %d orphan running task(s)", count)
        return count


# ── 默认 handler: MANUAL_CLOSE_ALL ───────────────────────────────────
@register_handler("MANUAL_CLOSE_ALL")
def _handle_manual_close_all(session, payload: dict) -> None:
    """payload: {account_id, trading_mode, reason, operator_user_id}。"""
    from src.controllers.dependencies import get_adapter
    from src.services.events.outbox import OutboxWriter
    from src.services.manual_ops import ManualOpsService

    trading_mode = payload.get("trading_mode", "testnet")
    adapter = get_adapter()
    outbox = OutboxWriter()
    svc = ManualOpsService(session=session, adapter=adapter, outbox=outbox)
    svc.manual_close_all(
        account_id=int(payload["account_id"]),
        trading_mode=trading_mode,
        reason=str(payload.get("reason", "scheduler-dispatch")),
        operator_user_id=int(payload["operator_user_id"]),
    )
