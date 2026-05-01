"""StrategyRouter V0.1 单路由测试。"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.models import AuditLog, Base
from src.strategy.ai_trader.pipeline import PipelineInput
from src.strategy.proposal import DecisionProposal
from src.strategy.router import StrategyRouter


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _StubAdapter:
    def __init__(self, proposal: DecisionProposal, decision_id: int | None = 999):
        self._p = proposal
        self._decision_id = decision_id
        self.call_count = 0

    def run(self, inp: PipelineInput) -> tuple[DecisionProposal, int | None]:
        self.call_count += 1
        return self._p, self._decision_id


def _input() -> PipelineInput:
    return PipelineInput(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        current_price=50000.0,
        indicators={}, factors={}, regime="trending_up",
        open_position=None,
        account_snapshot={"available_usdt": 10000.0, "daily_pnl": 0.0, "daily_pnl_pct": 0.0},
        factor_snapshot_id=42, atr=200.0,
    )


def _proposal() -> DecisionProposal:
    return DecisionProposal(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        action="HOLD", confidence=0.0,
        strategy_mode="ai_observation", source="ai_trader",
    )


def test_router_forwards_to_ai_trader(session):
    stub = _StubAdapter(_proposal(), decision_id=42)
    router = StrategyRouter(session, ai_trader=stub)
    proposal, decision_id = router.decide(_input())
    assert stub.call_count == 1
    assert proposal.action == "HOLD"
    assert decision_id == 42


def test_router_writes_audit_log_per_decision(session):
    stub = _StubAdapter(_proposal())
    router = StrategyRouter(session, ai_trader=stub)
    router.decide(_input())
    rows = session.execute(select(AuditLog)).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.action == "strategy_router_decide"
    assert row.resource_type == "strategy_route"
    assert row.resource_id == "BTCUSDT:1h"
    assert row.after_json["route"] == "ai_trader"
    assert row.after_json["regime"] == "trending_up"
    assert row.after_json["factor_snapshot_id"] == 42
    assert row.after_json["has_open_position"] is False


def test_router_audit_marks_open_position(session):
    stub = _StubAdapter(_proposal())
    router = StrategyRouter(session, ai_trader=stub)
    inp = _input()
    inp.open_position = {"quantity": 0.01, "entry_price": 50000}
    router.decide(inp)
    row = session.execute(select(AuditLog)).scalars().first()
    assert row.after_json["has_open_position"] is True


def test_router_returns_whatever_adapter_returns(session):
    """路由器不做二次加工——只转发 + 审计 (含 decision_id)."""
    p = DecisionProposal(
        account_id=1, symbol="X", timeframe="1h",
        action="OPEN_LONG", confidence=0.9,
        entry_type="MARKET", entry_price=1.0, stop_loss=0.9,
        take_profit=1.2, position_size_pct=0.1,
        strategy_mode="ai_trend", source="ai_trader",
    )
    stub = _StubAdapter(p, decision_id=7)
    router = StrategyRouter(session, ai_trader=stub)
    got_p, got_id = router.decide(_input())
    assert got_p is p
    assert got_id == 7
