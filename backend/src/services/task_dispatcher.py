"""TaskDispatcher — spec §4.9.1 前台 API 提任务 + scheduler 进程消费。

闭环:
  - enqueue: API 进程调用, 写 task_requests(PENDING) + LPUSH redis 队列
  - dispatch_loop: scheduler 进程主线程 BRPOP 消费, 路由到 handler
  - recover_orphans: scheduler 启动时把卡在 RUNNING 的标 FAILED (不重试, 人工 review);
    把超时仍 PENDING 的重新 LPUSH (从未执行过, 不违反"不自动重试"原则,
    mark_running CAS 保证即使队列里残留旧引用也不会重复执行)
  - 终态 (SUCCESS/FAILED) 写 task.status_changed outbox 事件 → EventShuttle → WS 实时层
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Callable, Optional

from src.cruds.task_request_crud import task_request_crud
from src.services.events.contracts import TaskStatusChanged
from src.services.events.outbox import OutboxWriter

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
        self._outbox = OutboxWriter()

    def _record_status_event(
        self, session, task, status: str, error_message: str | None = None,
    ) -> None:
        """终态写 task.status_changed outbox 事件 (与状态变更同事务, 失败不阻断主流程)。"""
        try:
            self._outbox.record(
                session,
                aggregate_type="task_request",
                aggregate_id=task.id,
                event=TaskStatusChanged(
                    task_id=task.id, task_type=task.task_type,
                    status=status, error_message=error_message,
                ),
                account_id=int((task.payload or {}).get("account_id", 1)),
                trading_mode=task.trading_mode,
                trace_id=f"task:{task.id}",
            )
        except Exception:
            logger.exception("record task.status_changed failed for task %s", task.id)

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
            err = f"NoHandler:{task_type}"
            with self._db_factory() as session:
                obj = task_request_crud.mark_failed(session, task_id, error_message=err)
                self._record_status_event(session, obj, "FAILED", err)
                session.commit()
            logger.error("No handler for task_type=%s (id=%s)", task_type, task_id)
            return

        try:
            with self._db_factory() as session:
                handler(session, payload)
                session.commit()
            with self._db_factory() as session:
                obj = task_request_crud.mark_success(session, task_id)
                self._record_status_event(session, obj, "SUCCESS")
                session.commit()
            logger.info("Task %s (%s) success", task_id, task_type)
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            logger.exception("Task %s (%s) failed: %s", task_id, task_type, err)
            try:
                with self._db_factory() as session:
                    obj = task_request_crud.mark_failed(session, task_id, error_message=err)
                    self._record_status_event(session, obj, "FAILED", err)
                    session.commit()
            except Exception:
                logger.exception("mark_failed itself failed for task %s", task_id)

    # ── recover_orphans (scheduler 启动时) ───────────────────────────
    def recover_orphans(self, threshold_seconds: int = 300) -> int:
        """启动恢复两类孤儿:

        - RUNNING 超时 → 标 FAILED (交易系统不自动重试, 人工 review)
        - PENDING 超时 → 重新 LPUSH (enqueue 写库成功但 LPUSH 丢失的场景;
          任务从未执行过, 重推不算重试; mark_running CAS 防重复消费)
        """
        count = 0
        requeue_ids: list[int] = []
        with self._db_factory() as session:
            orphan_msg = "orphaned (scheduler restart)"
            orphans = task_request_crud.find_orphan_running(session, threshold_seconds)
            for obj in orphans:
                failed = task_request_crud.mark_failed(session, obj.id, error_message=orphan_msg)
                self._record_status_event(session, failed, "FAILED", orphan_msg)
                count += 1
            pending = task_request_crud.find_orphan_pending(session, threshold_seconds)
            requeue_ids = [obj.id for obj in pending]
            session.commit()
        for task_id in requeue_ids:
            self._redis.lpush(self._queue_key, json.dumps({"task_id": task_id}))
        if count:
            logger.warning("Recovered %d orphan running task(s)", count)
        if requeue_ids:
            logger.warning("Re-queued %d orphan pending task(s): %s", len(requeue_ids), requeue_ids)
        return count


# ── API 进程单例 (controller 入队用; scheduler 进程在 start_scheduler.py 自行构造) ──
_default_dispatcher: Optional[TaskDispatcher] = None


def get_task_dispatcher() -> TaskDispatcher:
    """API 进程懒加载单例: sessionmaker + 同步 redis + 配置队列 key。"""
    global _default_dispatcher
    if _default_dispatcher is None:
        from src.configs import get_app_config
        from src.db.engines import get_session_factory
        from src.utils.redis import get_redis_client

        cfg = get_app_config()
        _default_dispatcher = TaskDispatcher(
            db_factory=get_session_factory(),
            redis_client=get_redis_client(),
            queue_key=cfg.TASK_QUEUE_KEY,
        )
    return _default_dispatcher


def reset_task_dispatcher() -> None:
    """单测使用: 重置单例。生产代码不应调用。"""
    global _default_dispatcher
    _default_dispatcher = None


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
