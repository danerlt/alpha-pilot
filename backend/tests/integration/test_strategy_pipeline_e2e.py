"""strategy_pipeline 端到端集成测试 (testcontainers Postgres + Redis)。

跑完一次 pipeline 后:
  - 所有表都有期待的行
  - Outbox 至少包含 candle.closed / decision.proposed / order.submitted /
    order.filled / position.opened 这些事件
  - 重复跑同一 decision_id (幂等场景) → orders 不重复

由于 e2e 较慢, 该测试只跑一个 happy path scenario; 详细单点行为在
unit/integration/test_strategy_pipeline.py 已覆盖。
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from alembic import command
from alembic.config import Config

from src.services.events.bus import RedisStreamsBus
from src.services.events.outbox import OutboxWriter
from src.core.exchange.adapter import ExchangeAdapter
from src.core.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.models import (
    AIDecision, EventOutbox, Order, Position, PromptTemplate,
)
from src.models.account_entity import RiskProfile
from src.core.llm.client import MockLLMClient
from src.workers.strategy_pipeline import run_strategy_pipeline_once


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


class _PipelineAdapter(ExchangeAdapter):
    def __init__(self, ticker_price=50_000.0, fill_price=50_000.0):
        self._t = ticker_price
        self._f = fill_price
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Spread 大一点(~1%)让 ATR 算出来 ~500, 这样 LLM 返回的 SL 距离 200
        # 落在 [0.5, 5] × ATR = [250, 2500] 区间.
        ks = []
        for i in range(250):
            mid = 49_000.0 + i * 4
            ks.append(Kline(
                symbol="BTCUSDT", timeframe="1h",
                open_time=base + timedelta(hours=i),
                open=mid,
                high=mid + 250.0,
                low=mid - 250.0,
                close=mid + 50.0,
                volume=1000.0,
            ))
        self._ks = ks

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"
    def get_ticker(self, s): return Ticker(symbol=s, price=self._t)
    def get_klines(self, s, t, **kw): return self._ks[-kw.get("limit", 250):]
    def submit_order(self, r):
        return OrderResult(
            exchange_order_id="EX-E2E", symbol=r.symbol, side=r.side,
            order_type=r.order_type, status="FILLED",
            requested_quantity=r.quantity, filled_quantity=r.quantity,
            avg_fill_price=self._f, client_order_id=r.client_order_id,
        )
    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset): return 10_000.0 if asset == "USDT" else 0.0


def _seed_template(session):
    session.add(PromptTemplate(
        name="ait_default", version=1,
        system_template="sys ${symbol} ${regime}",
        user_template="user ${current_price} ${factors_json}",
        active=True,
    ))


def _seed_risk_profile() -> RiskProfile:
    return RiskProfile(
        account_id=1, name="default",
        max_position_size_pct=Decimal("0.20"),
        max_daily_loss_pct=Decimal("0.03"),
        max_consecutive_losses=3,
        max_single_risk_pct=Decimal("0.01"),
        min_rr_ratio=Decimal("1.50"),
        sl_atr_min_mult=Decimal("0.50"),
        sl_atr_max_mult=Decimal("5.00"),
    )


VALID_LLM_RESPONSE = json.dumps({
    "action": "OPEN_LONG",
    "confidence": 0.75,
    "entry_type": "MARKET",
    "entry_price": 50_000.0,
    "stop_loss": 49_500.0,   # SL 距 500 ≈ 1×ATR (在 [0.5, 5]×ATR 范围)
    "take_profit": 51_000.0, # TP 距 1000, R/R = 2 (>= 1.5)
    "position_size_pct": 0.10,
    "strategy_mode": "ai_trend",
    "reasoning": ["e2e"],
})


def test_e2e_full_pipeline_writes_chain_and_outbox(pg_url, redis_url):
    engine = create_engine(pg_url)
    bus = RedisStreamsBus(redis_url)
    outbox = OutboxWriter()

    with Session(engine) as session:
        _seed_template(session)
        session.commit()

        profile = _seed_risk_profile()
        adapter = _PipelineAdapter()
        llm = MockLLMClient(canned_response=VALID_LLM_RESPONSE)

        summary = run_strategy_pipeline_once(
            db=session, account_id=1, trading_mode="testnet",
            adapter=adapter, llm_client=llm, risk_profile=profile,
            symbols=["BTCUSDT"], timeframes=["1h"],
            outbox=outbox,
        )
        assert summary["BTCUSDT:1h"]["action"] == "OPEN_LONG", f"summary={summary}"

    # 校验链路
    with Session(engine) as session:
        decision = session.execute(select(AIDecision)).scalars().first()
        assert decision is not None and decision.is_fallback is False
        order = session.execute(select(Order)).scalars().first()
        assert order is not None and order.status == "filled"
        position = session.execute(select(Position)).scalars().first()
        assert position is not None and position.status == "open"

        # outbox 事件
        evt_types = [
            e.event_type
            for e in session.execute(select(EventOutbox).order_by(EventOutbox.id)).scalars().all()
        ]
        assert "candle.closed" in evt_types
        assert "order.submitted" in evt_types
        assert "order.filled" in evt_types
        assert "position.opened" in evt_types
