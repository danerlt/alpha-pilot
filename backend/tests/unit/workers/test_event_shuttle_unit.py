"""EventShuttle 单元测试 (不依赖 Redis testcontainer).

用 mock _BusLike 走纯逻辑路径, 验证 max_failed_attempts 可配 + 死信失败时
仍正确标记 published_at (Plan 5 codereview I10).
"""
from __future__ import annotations

import os

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.events.contracts import EventEnvelope
from src.events.ids import new_event_id
from src.models import Base, EventOutbox
from src.workers.event_shuttle import DEFAULT_MAX_FAILED_ATTEMPTS, EventShuttle


@pytest.fixture
def engine():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", os.environ.get("TEST_DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))))
    Base.metadata.create_all(eng)
    yield eng


def _add_outbox_row(engine, event_type: str = "candle.closed") -> int:
    """添加一行未 publish 的 event_outbox, 返回 id."""
    with Session(engine) as s:
        eid = new_event_id()
        envelope = EventEnvelope(
            event_id=eid, account_id=1, trading_mode="testnet",
            occurred_at=datetime.now(timezone.utc),
            trace_id="t-test", schema_version=1,
            event_type=event_type, payload={"k": "v"},
        )
        row = EventOutbox(
            aggregate_type="x", aggregate_id=1,
            event_type=event_type, event_id=eid,
            payload_json=envelope.model_dump(mode="json"),
        )
        s.add(row)
        s.commit()
        return row.id


class _OkBus:
    """publish 成功; dead_letter 不应被调用."""
    def __init__(self):
        self.published: list[tuple[str, EventEnvelope]] = []
        self.dead_lettered: list[tuple[str, EventEnvelope, str]] = []

    def publish(self, stream, envelope, **kw):
        self.published.append((stream, envelope))
        return "1-0"

    def dead_letter(self, stream, envelope, reason):
        self.dead_lettered.append((stream, envelope, reason))


class _FailingBus:
    """publish 永远抛错; dead_letter 可控成功/失败."""
    def __init__(self, *, dead_letter_ok: bool = True):
        self.publish_calls = 0
        self.dead_letter_calls = 0
        self._dl_ok = dead_letter_ok

    def publish(self, stream, envelope, **kw):
        self.publish_calls += 1
        raise RuntimeError("simulated publish failure")

    def dead_letter(self, stream, envelope, reason):
        self.dead_letter_calls += 1
        if not self._dl_ok:
            raise RuntimeError("dead_letter also broke")


def test_default_max_failed_attempts_constant():
    assert DEFAULT_MAX_FAILED_ATTEMPTS == 3


def test_drain_once_marks_published_on_success(engine):
    rid = _add_outbox_row(engine)
    bus = _OkBus()
    shuttle = EventShuttle(engine, bus, max_failed_attempts=3)

    n = shuttle.drain_once()
    assert n == 1
    assert len(bus.published) == 1
    assert bus.dead_lettered == []
    with Session(engine) as s:
        row = s.get(EventOutbox, rid)
        assert row.published_at is not None
        assert row.failed_attempts == 0


def test_failure_increments_attempts_no_dead_letter_yet(engine):
    rid = _add_outbox_row(engine)
    bus = _FailingBus()
    shuttle = EventShuttle(engine, bus, max_failed_attempts=3)

    shuttle.drain_once()
    with Session(engine) as s:
        row = s.get(EventOutbox, rid)
        assert row.failed_attempts == 1
        assert row.published_at is None  # 未到阈值, 不死信
        assert "simulated publish failure" in (row.last_error or "")
    assert bus.dead_letter_calls == 0


def test_dead_letter_after_max_failed_attempts(engine):
    rid = _add_outbox_row(engine)
    bus = _FailingBus()
    shuttle = EventShuttle(engine, bus, max_failed_attempts=2)

    # 第 1 次: failed=1, 不死信
    shuttle.drain_once()
    # 第 2 次: failed=2, 死信
    shuttle.drain_once()
    assert bus.dead_letter_calls == 1
    with Session(engine) as s:
        row = s.get(EventOutbox, rid)
        assert row.failed_attempts == 2
        assert row.published_at is not None  # 死信成功 → 标 published_at


def test_dead_letter_failure_still_marks_published(engine):
    """关键场景 (codereview I10 修): dead_letter 也失败时, 必须仍标
    published_at, 否则会无限循环重试 dead_letter, 卡住后续行."""
    rid = _add_outbox_row(engine)
    bus = _FailingBus(dead_letter_ok=False)
    shuttle = EventShuttle(engine, bus, max_failed_attempts=1)

    shuttle.drain_once()  # failed=1, 死信但失败
    assert bus.dead_letter_calls == 1
    with Session(engine) as s:
        row = s.get(EventOutbox, rid)
        assert row.published_at is not None  # 必须被标, 防卡死
        assert "dead_letter_failed" in (row.last_error or "")

    # 再 drain 一次, 已 published 行不应被再次处理
    shuttle.drain_once()
    assert bus.dead_letter_calls == 1  # 没有新调用


def test_max_failed_attempts_zero_means_first_failure_is_dead_letter(engine):
    rid = _add_outbox_row(engine)
    bus = _FailingBus()
    shuttle = EventShuttle(engine, bus, max_failed_attempts=0)

    shuttle.drain_once()
    # failed_attempts 1 >= 0 → 立刻死信
    assert bus.dead_letter_calls == 1
    with Session(engine) as s:
        row = s.get(EventOutbox, rid)
        assert row.published_at is not None
