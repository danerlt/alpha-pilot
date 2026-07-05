"""DecisionProgressEmitter 单测 — 独立 session 即时落 outbox + 异常静默。"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.models import Base
from src.models.event_store import EventOutbox
from src.services.events.progress import DecisionProgressEmitter


@pytest.fixture
def engine():
    # 全局 conftest 已把 TEST_DATABASE_URL 指到本地 PG 测试库
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def emitter(engine):
    factory = sessionmaker(bind=engine)
    return DecisionProgressEmitter(
        session_factory=factory, account_id=1, trading_mode="testnet",
    )


def test_emit_writes_outbox_row_immediately(engine, emitter):
    emitter.emit(
        "snapshot", "start",
        symbol="BTCUSDT", timeframe="1h", trace_id="t1",
    )
    with Session(engine) as s:
        rows = s.execute(select(EventOutbox)).scalars().all()
        assert len(rows) == 1
        row = rows[0]
        assert row.event_type == "decision.progress"
        assert row.payload_json["payload"]["stage"] == "snapshot"
        assert row.payload_json["payload"]["status"] == "start"
        assert row.payload_json["trace_id"] == "t1"


def test_emit_with_decision_id_and_detail(engine, emitter):
    emitter.emit(
        "reasoning", "done",
        symbol="BTCUSDT", timeframe="1h", trace_id="t2",
        decision_id=42, detail={"action": "HOLD"},
    )
    with Session(engine) as s:
        row = s.execute(select(EventOutbox)).scalars().one()
        assert row.payload_json["payload"]["decision_id"] == 42
        assert row.payload_json["payload"]["detail"] == {"action": "HOLD"}


def test_fail_current_uses_last_started_stage(engine, emitter):
    emitter.emit("guard", "start", symbol="ETHUSDT", timeframe="1h", trace_id="t3")
    emitter.fail_current("boom")
    with Session(engine) as s:
        rows = s.execute(
            select(EventOutbox).order_by(EventOutbox.id)
        ).scalars().all()
        assert len(rows) == 2
        fail = rows[-1].payload_json["payload"]
        assert fail["stage"] == "guard"
        assert fail["status"] == "fail"
        assert fail["detail"] == {"error": "boom"}


def test_fail_current_without_prior_start_is_noop(engine, emitter):
    emitter.fail_current("boom")
    with Session(engine) as s:
        assert s.execute(select(EventOutbox)).scalars().all() == []


def test_emit_swallows_session_factory_errors(engine):
    def _broken_factory():
        raise RuntimeError("db down")

    em = DecisionProgressEmitter(
        session_factory=_broken_factory, account_id=1, trading_mode="testnet",
    )
    # 不应抛出
    em.emit("snapshot", "start", symbol="BTCUSDT", timeframe="1h", trace_id="t4")
