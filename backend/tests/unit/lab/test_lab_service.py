"""LabService + ShadowRunner 单测 (handoff P5)。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.common.exception.errors import ServiceException
from src.models import Base
from src.models.decision import AIDecision
from src.models.lab_candidate import LabCandidate
from src.models.shadow import ShadowDecision, ShadowEvaluation
from src.services.lab.lab_service import LabService
from src.services.lab.shadow_runner import (
    ShadowRunner,
    simulate_pnl_pct,
    transform_proposal,
)


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _TickerAdapter:
    def __init__(self, price=51_000.0):
        self._price = price

    def get_ticker(self, symbol):
        from src.core.exchange.types import Ticker

        return Ticker(symbol=symbol, price=self._price)


def _submit(session, **kw) -> LabCandidate:
    defaults = dict(
        name="SL 收紧 0.8x", description="d", params={"sl_mult": 0.8},
        trading_mode="testnet", user_id=1,
    )
    defaults.update(kw)
    return LabService(session).submit(**defaults)


# ── 纯函数 ──────────────────────────────────────────────────────────────


def test_transform_proposal_sl_tp_size():
    base = {
        "action": "OPEN_LONG", "confidence": 0.7,
        "entry_price": 100.0, "stop_loss": 90.0, "take_profit": 120.0,
        "position_size_pct": 0.1,
    }
    out = transform_proposal(base, {"sl_mult": 0.5, "tp_mult": 2.0, "size_scale": 2.0})
    assert out["stop_loss"] == 95.0       # 距离 10 → 5
    assert out["take_profit"] == 140.0    # 距离 20 → 40
    assert out["position_size_pct"] == 0.2


def test_transform_min_confidence_degrades_to_hold():
    base = {"action": "OPEN_LONG", "confidence": 0.5, "entry_price": 100.0}
    out = transform_proposal(base, {"min_confidence": 0.6})
    assert out["action"] == "HOLD"


def test_simulate_pnl_pct_paths():
    p = {"action": "OPEN_LONG", "entry_price": 100.0, "stop_loss": 90.0,
         "take_profit": 120.0, "position_size_pct": 0.1}
    assert simulate_pnl_pct(p, 85.0) == pytest.approx(-0.01)   # 触 SL: -10%×0.1
    assert simulate_pnl_pct(p, 130.0) == pytest.approx(0.02)   # 触 TP: +20%×0.1
    assert simulate_pnl_pct(p, 105.0) == pytest.approx(0.005)  # 浮动: +5%×0.1
    assert simulate_pnl_pct({"action": "HOLD"}, 100.0) is None


# ── 生命周期 ────────────────────────────────────────────────────────────


def test_lifecycle_submit_start_terminate(session):
    row = _submit(session)
    assert row.stage == "QUEUED"
    svc = LabService(session)
    row = svc.start_shadow(candidate_id=row.id, user_id=1, trading_mode="testnet")
    assert row.stage == "SHADOW" and row.shadow_run_id
    row = svc.terminate(candidate_id=row.id, user_id=1, trading_mode="testnet", reason="不做了")
    assert row.stage == "RETIRED"
    # history 时间线含三条
    actions = [h["action"] for h in svc.history(trading_mode="testnet")]
    assert actions[:3] == ["retire", "start", "submit"]


def test_promote_gate_blocks_early_shadow(session):
    svc = LabService(session)
    row = _submit(session)
    row = svc.start_shadow(candidate_id=row.id, user_id=1, trading_mode="testnet")
    with pytest.raises(ServiceException, match="门槛"):
        svc.promote(candidate_id=row.id, user_id=1, trading_mode="testnet")


def _make_promotable(session, svc) -> LabCandidate:
    """影子期 100% + 3 条正收益评估 → 达标候选。"""
    row = _submit(session)
    row = svc.start_shadow(candidate_id=row.id, user_id=1, trading_mode="testnet")
    row.shadow_started_at = datetime.now(tz=timezone.utc) - timedelta(days=15)
    for i in range(3):
        sd = ShadowDecision(
            shadow_run_id=row.shadow_run_id, real_decision_id=None,
            proposal_json={"symbol": "BTCUSDT", "action": "OPEN_LONG", "entry_price": 100.0},
        )
        session.add(sd)
        session.flush()
        session.add(ShadowEvaluation(
            shadow_decision_id=sd.id, shadow_pnl_sim=0.01,
            evaluated_at=datetime.now(tz=timezone.utc),
        ))
    session.commit()
    return row


def test_promote_gate_passes_then_canary_then_live(session):
    svc = LabService(session)
    row = _make_promotable(session, svc)
    detail = svc.candidate_detail(row)
    assert detail["promote_eligible"] is True
    row = svc.promote(candidate_id=row.id, user_id=9, trading_mode="testnet")
    assert row.stage == "CANARY"
    row = svc.promote(candidate_id=row.id, user_id=9, trading_mode="testnet")
    assert row.stage == "LIVE"


def test_rollback_only_from_canary(session):
    svc = LabService(session)
    row = _submit(session)
    with pytest.raises(ServiceException):
        svc.rollback(candidate_id=row.id, reason="x", trading_mode="testnet")


# ── ShadowRunner ────────────────────────────────────────────────────────


def _real_decision(session, **kw) -> AIDecision:
    defaults = dict(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        decided_at=datetime.now(tz=timezone.utc), action="OPEN_LONG",
        confidence=0.7, entry_price=50_000.0, stop_loss=49_000.0,
        take_profit=52_000.0, position_size_pct=0.1,
        strategy_mode="ai_trend", is_fallback=False, source="ai_trader",
    )
    defaults.update(kw)
    d = AIDecision(**defaults)
    session.add(d)
    session.commit()
    return d


def test_shadow_runner_mirrors_and_evaluates(session):
    svc = LabService(session)
    row = _submit(session, params={"sl_mult": 0.5})
    row = svc.start_shadow(candidate_id=row.id, user_id=1, trading_mode="testnet")
    _real_decision(session)

    runner = ShadowRunner(session, _TickerAdapter(price=51_000.0))
    stats = runner.run_once(trading_mode="testnet")
    assert stats["mirrored"] == 1
    assert stats["evaluated"] == 1

    sd = session.execute(select(ShadowDecision)).scalars().one()
    assert sd.proposal_json["stop_loss"] == 49_500.0  # SL 距离 1000 → 500
    ev = session.execute(select(ShadowEvaluation)).scalars().one()
    assert float(ev.shadow_pnl_sim) == pytest.approx(0.002)  # +2%×0.1

    # 幂等: 再跑一轮不重复镜像, 评估更新既有行
    stats2 = runner.run_once(trading_mode="testnet")
    assert stats2["mirrored"] == 0
    assert len(session.execute(select(ShadowEvaluation)).scalars().all()) == 1


def test_canary_auto_rollback_on_drawdown(session):
    from decimal import Decimal

    from src.models.account import AccountSnapshot
    from src.models.account_entity import RiskProfile

    session.add(RiskProfile(
        account_id=1, name="default", version=1, active=True,
        max_position_size_pct=Decimal("0.20"), max_daily_loss_pct=Decimal("0.03"),
        max_consecutive_losses=3, max_single_risk_pct=Decimal("0.01"),
        min_rr_ratio=Decimal("1.50"), sl_atr_min_mult=Decimal("0.50"),
        sl_atr_max_mult=Decimal("5.00"),
    ))
    session.add(AccountSnapshot(
        account_id=1, trading_mode="testnet",
        snapshot_at=datetime.now(tz=timezone.utc),
        total_balance_usdt=10_000, available_balance_usdt=10_000,
        unrealized_pnl=0, daily_pnl=-250, daily_pnl_pct=-0.025,  # 超 0.03×0.8=0.024
    ))
    session.commit()

    svc = LabService(session)
    row = _make_promotable(session, svc)
    row = svc.promote(candidate_id=row.id, user_id=9, trading_mode="testnet")
    assert row.stage == "CANARY"

    stats = ShadowRunner(session, _TickerAdapter()).run_once(trading_mode="testnet")
    assert stats["rolled_back"] == 1
    session.expire_all()
    assert session.get(LabCandidate, row.id).stage == "ROLLED_BACK"
    assert "canary_drawdown" in session.get(LabCandidate, row.id).rollback_reason
    # 时间线里有 rollback + system 操作者
    hist = svc.history(trading_mode="testnet")
    rb = next(h for h in hist if h["action"] == "rollback")
    assert rb["operator"] == "system"
