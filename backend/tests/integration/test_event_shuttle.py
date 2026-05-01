"""End-to-end: write to event_outbox -> shuttle publishes to Redis Streams -> consumer sees it."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from alembic import command
from alembic.config import Config

from src.services.events.bus import RedisStreamsBus
from src.services.events.contracts import CandleClosed
from src.services.events.outbox import OutboxWriter
from src.workers.event_shuttle import EventShuttle


@pytest.fixture(scope="module")
def pg_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        cfg = Config(os.path.join(backend_dir, "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", url)
        cfg.set_main_option("script_location", os.path.join(backend_dir, "migrations"))
        command.upgrade(cfg, "head")
        yield url


@pytest.fixture(scope="module")
def redis_url():
    with RedisContainer("redis:7-alpine") as rc:
        host = rc.get_container_host_ip()
        port = rc.get_exposed_port(rc.port)
        yield f"redis://{host}:{port}/0"


def test_outbox_to_streams_roundtrip(pg_url, redis_url):
    engine = create_engine(pg_url)
    bus = RedisStreamsBus(redis_url)
    bus.ensure_group("candle.closed", "test-consumer")

    writer = OutboxWriter()
    with Session(engine) as s:
        evt = CandleClosed(
            symbol="BTCUSDT", timeframe="1h",
            open_time=datetime.now(timezone.utc),
            open=1, high=2, low=0.5, close=1.5, volume=100,
        )
        writer.record(
            s, aggregate_type="candle", aggregate_id=None, event=evt,
            account_id=1, trading_mode="testnet", trace_id="smoke-trace-1",
        )
        s.commit()

    shuttle = EventShuttle(engine=engine, bus=bus, stream_for_event=lambda e: e)
    published = shuttle.drain_once(batch_size=10)
    assert published == 1

    msgs = list(bus.consume("candle.closed", "test-consumer", "c1", count=5, block_ms=500))
    assert len(msgs) == 1
    _, env = msgs[0]
    assert env.event_type == "candle.closed"
    assert env.payload["symbol"] == "BTCUSDT"


def test_shuttle_marks_published_at(pg_url, redis_url):
    from src.models import EventOutbox
    engine = create_engine(pg_url)
    bus = RedisStreamsBus(redis_url)

    writer = OutboxWriter()
    with Session(engine) as s:
        evt = CandleClosed(
            symbol="ETHUSDT", timeframe="1h",
            open_time=datetime.now(timezone.utc),
            open=1, high=2, low=0.5, close=1.5, volume=100,
        )
        writer.record(
            s, aggregate_type="candle", aggregate_id=None, event=evt,
            account_id=1, trading_mode="testnet", trace_id="pa-check",
        )
        s.commit()

    shuttle = EventShuttle(engine=engine, bus=bus, stream_for_event=lambda e: e)
    shuttle.drain_once()

    with Session(engine) as s:
        rows = (
            s.query(EventOutbox)
            .filter(EventOutbox.payload_json["trace_id"].as_string() == "pa-check")
            .all()
        )
        # PostgreSQL JSON ops vary; fall back to manual filter if the above fails.
        if not rows:
            all_rows = s.query(EventOutbox).all()
            rows = [r for r in all_rows if r.payload_json.get("trace_id") == "pa-check"]
        assert len(rows) == 1
        assert rows[0].published_at is not None


def test_shuttle_dead_letters_after_max_attempts(pg_url, redis_url):
    """Simulate a broken bus: failed_attempts accrues, then row ends up published_at set
    to avoid infinite reprocessing after dead-lettering."""
    from src.models import EventOutbox
    engine = create_engine(pg_url)
    real_bus = RedisStreamsBus(redis_url)

    class BrokenBus:
        def __init__(self, real):
            self.real = real
            self.calls = 0
        def publish(self, stream, envelope, **kw):
            self.calls += 1
            raise RuntimeError("simulated broken bus")
        def dead_letter(self, stream, envelope, reason):
            return self.real.dead_letter(stream, envelope, reason)

    broken = BrokenBus(real_bus)

    writer = OutboxWriter()
    with Session(engine) as s:
        evt = CandleClosed(
            symbol="XRPUSDT", timeframe="1h",
            open_time=datetime.now(timezone.utc),
            open=1, high=2, low=0.5, close=1.5, volume=100,
        )
        writer.record(
            s, aggregate_type="candle", aggregate_id=None, event=evt,
            account_id=1, trading_mode="testnet", trace_id="dl-check",
        )
        s.commit()

    shuttle = EventShuttle(engine=engine, bus=broken, stream_for_event=lambda e: e)
    # Drain enough times to exceed the MAX_FAILED_ATTEMPTS threshold.
    for _ in range(5):
        shuttle.drain_once()

    with Session(engine) as s:
        all_rows = s.query(EventOutbox).all()
        target = [r for r in all_rows if r.payload_json.get("trace_id") == "dl-check"]
        assert len(target) == 1
        row = target[0]
        assert row.failed_attempts >= 3
        # After dead-lettering, published_at is set so we don't infinite loop.
        assert row.published_at is not None
