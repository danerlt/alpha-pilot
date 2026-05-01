"""TaskDispatcher 单测 (spec §4.9.1)。"""
from __future__ import annotations

import contextlib
import threading
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.cruds.task_request_crud import task_request_crud
from src.models.task_request import TaskRequest
from src.services.task_dispatcher import HANDLERS, TaskDispatcher, register_handler


@pytest.fixture
def db_factory(pg_session):
    """db_factory: 每次调用返回同一个 pg_session (commit/rollback 真走 PG, 不 close)。"""
    @contextlib.contextmanager
    def _factory():
        try:
            yield pg_session
        except Exception:
            pg_session.rollback()
            raise
    return _factory


@pytest.fixture
def fake_redis():
    return MagicMock()


def test_enqueue_writes_row_and_pushes_redis(pg_session, db_factory, fake_redis):
    dispatcher = TaskDispatcher(db_factory=db_factory, redis_client=fake_redis, queue_key="t:q")
    task_id = dispatcher.enqueue("MANUAL_CLOSE_ALL", {"account_id": 1}, trading_mode="testnet")

    obj = pg_session.get(TaskRequest, task_id)
    assert obj is not None
    assert obj.status == "PENDING"
    assert obj.task_type == "MANUAL_CLOSE_ALL"
    assert obj.payload == {"account_id": 1}
    assert obj.trading_mode == "testnet"

    assert fake_redis.lpush.call_count == 1
    args, _ = fake_redis.lpush.call_args
    assert args[0] == "t:q"
    assert f'"task_id": {task_id}' in args[1]


def test_dispatch_loop_runs_handler_on_success(pg_session, db_factory, fake_redis):
    seen = {}

    @register_handler("UNIT_TEST_OK")
    def _handler(session, payload):
        seen["payload"] = payload

    try:
        # 先入队
        dispatcher = TaskDispatcher(db_factory=db_factory, redis_client=fake_redis, queue_key="t:q")
        task_id = dispatcher.enqueue("UNIT_TEST_OK", {"hello": "world"})

        # 模拟 BRPOP: 第一次返队列项, 第二次返 None 让循环退出
        import json as _json
        fake_redis.brpop.side_effect = [
            ("t:q", _json.dumps({"task_id": task_id})),
            None,
        ]
        stop_flag = threading.Event()

        def _stop_after_two_calls(*a, **kw):
            # brpop side_effect 用尽后, 我们手动设 stop_flag
            ...
        # 跑一个线程, 第二次 None 之后再 set stop_flag
        def _runner():
            dispatcher.dispatch_loop(stop_flag)

        t = threading.Thread(target=_runner)
        t.start()
        # 给一点时间消费两次 brpop
        import time as _t
        _t.sleep(0.3)
        stop_flag.set()
        t.join(timeout=3)

        pg_session.expire_all()
        obj = pg_session.get(TaskRequest, task_id)
        assert obj.status == "SUCCESS"
        assert obj.started_at is not None
        assert obj.finished_at is not None
        assert seen["payload"] == {"hello": "world"}
    finally:
        HANDLERS.pop("UNIT_TEST_OK", None)


def test_dispatch_loop_marks_failed_on_handler_exception(pg_session, db_factory, fake_redis):
    @register_handler("UNIT_TEST_FAIL")
    def _handler(session, payload):
        raise RuntimeError("boom-detail")

    try:
        dispatcher = TaskDispatcher(db_factory=db_factory, redis_client=fake_redis, queue_key="t:q")
        task_id = dispatcher.enqueue("UNIT_TEST_FAIL", {})

        import json as _json
        fake_redis.brpop.side_effect = [
            ("t:q", _json.dumps({"task_id": task_id})),
            None,
        ]
        stop_flag = threading.Event()

        def _runner():
            dispatcher.dispatch_loop(stop_flag)

        t = threading.Thread(target=_runner)
        t.start()
        import time as _t
        _t.sleep(0.3)
        stop_flag.set()
        t.join(timeout=3)

        pg_session.expire_all()
        obj = pg_session.get(TaskRequest, task_id)
        assert obj.status == "FAILED"
        assert "RuntimeError" in (obj.error_message or "")
        assert "boom-detail" in (obj.error_message or "")
    finally:
        HANDLERS.pop("UNIT_TEST_FAIL", None)


def test_recover_orphans_marks_old_running_as_failed(pg_session, db_factory, fake_redis):
    # 直接插一条 RUNNING + started_at 远早于 now-300s
    obj = TaskRequest(
        task_type="UNIT_TEST_ORPHAN",
        payload={},
        status="RUNNING",
        attempts=1,
        started_at=datetime.now(timezone.utc) - timedelta(seconds=600),
        trading_mode="testnet",
    )
    pg_session.add(obj)
    pg_session.commit()
    task_id = obj.id

    dispatcher = TaskDispatcher(db_factory=db_factory, redis_client=fake_redis, queue_key="t:q")
    count = dispatcher.recover_orphans(threshold_seconds=300)

    assert count == 1
    pg_session.expire_all()
    refreshed = pg_session.get(TaskRequest, task_id)
    assert refreshed.status == "FAILED"
    assert "orphaned" in (refreshed.error_message or "")
