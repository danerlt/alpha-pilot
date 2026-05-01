"""End-to-end smoke test for the full Plan 1 foundation stack.

Scenario (exercises every primitive Plan 1 produces):

  1. Postgres + Redis containers up → run all Alembic migrations
  2. Write a Position AND record a PositionOpened event via OutboxWriter
     inside the same DB transaction
  3. EventShuttle.drain_once() publishes the row to Redis Streams and
     marks published_at
  4. Consume from Redis Streams via RedisStreamsBus.consume() with a
     group, verify envelope integrity
  5. InboxGuard.claim() succeeds once, blocks second attempt
  6. Ack the message

If this test is green, the foundation contracts are sound and Plan 2 can
build strategy / execution / pipeline code on top.
"""
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
from src.services.events.contracts import EventEnvelope, PositionOpened
from src.services.events.inbox import InboxGuard
from src.services.events.outbox import OutboxWriter
from src.models import Position
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


def test_full_foundation_stack(pg_url, redis_url):
    engine = create_engine(pg_url)
    bus = RedisStreamsBus(redis_url)
    stream = "position.opened"
    bus.ensure_group(stream, "smoke-consumer")

    writer = OutboxWriter()

    # 1. Write Position AND outbox row in the same transaction.
    with Session(engine) as s:
        pos = Position(
            trading_mode="testnet",
            account_id=1,
            symbol="BTCUSDT",
            quantity=0.01,
            entry_price=100,
            stop_loss=95,
            opened_at=datetime.now(timezone.utc),
        )
        s.add(pos)
        s.flush()  # get pos.id before referencing in the event

        evt = PositionOpened(
            position_id=pos.id,
            symbol=pos.symbol,
            quantity=float(pos.quantity),
            entry_price=float(pos.entry_price),
            stop_loss=float(pos.stop_loss),
        )
        writer.record(
            s,
            aggregate_type="position",
            aggregate_id=pos.id,
            event=evt,
            account_id=1,
            trading_mode="testnet",
            trace_id="smoke-trace-1",
        )
        s.commit()

    # 2. Shuttle drains outbox → Streams.
    shuttle = EventShuttle(engine=engine, bus=bus, stream_for_event=lambda e: e)
    published = shuttle.drain_once()
    assert published == 1

    # 3. Consume from Streams and verify envelope integrity.
    messages = list(bus.consume(stream, "smoke-consumer", "c1", count=5, block_ms=500))
    assert len(messages) == 1
    msg_id, envelope = messages[0]
    assert isinstance(envelope, EventEnvelope)
    assert envelope.event_type == "position.opened"
    assert envelope.payload["symbol"] == "BTCUSDT"
    assert envelope.trace_id == "smoke-trace-1"

    # 4. InboxGuard idempotency: first claim wins, second is blocked.
    guard = InboxGuard(consumer_name="smoke-consumer")
    with Session(engine) as s:
        assert guard.claim(s, envelope.event_id) is True
        s.commit()
    with Session(engine) as s:
        assert guard.claim(s, envelope.event_id) is False

    # 5. Ack the message.
    bus.ack(stream, "smoke-consumer", msg_id)
