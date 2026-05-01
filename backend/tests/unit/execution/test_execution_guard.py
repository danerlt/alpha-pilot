"""ExecutionGuard 10 条规则链单测。"""
from __future__ import annotations

import os

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.execution.guard.execution_guard import ExecutionGuard, GuardDecision
from src.shared.enums import PositionStatus
from src.models import Base, Position, RiskEvent, Trade
from src.models.account_entity import RiskProfile
from src.strategy.proposal import DecisionProposal


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def profile() -> RiskProfile:
    """V0.1 默认 risk profile, 不持久化."""
    p = RiskProfile(
        account_id=1, name="default",
        max_position_size_pct=Decimal("0.20"),
        max_daily_loss_pct=Decimal("0.03"),
        max_consecutive_losses=3,
        max_single_risk_pct=Decimal("0.01"),
        min_rr_ratio=Decimal("1.50"),
        sl_atr_min_mult=Decimal("0.50"),
        sl_atr_max_mult=Decimal("5.00"),
    )
    return p


def _open_long(
    *, entry=50000.0, sl=49800.0, tp=50500.0, size=0.1,
) -> DecisionProposal:
    """合理基线: SL 距离 200, TP 500 → R/R = 2.5"""
    return DecisionProposal(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        action="OPEN_LONG", confidence=0.7,
        entry_type="MARKET", entry_price=entry,
        stop_loss=sl, take_profit=tp,
        position_size_pct=size,
        strategy_mode="ai_trend", source="ai_trader",
    )


def _check(
    session, profile, proposal, *,
    regime="trending_up",
    available=10_000.0, daily_pnl=0.0, daily_pnl_pct=0.0,
    atr=200.0, review_rejected=False,
):
    g = ExecutionGuard(session, risk_profile=profile)
    return g.check(
        proposal=proposal, trading_mode="testnet",
        current_price=proposal.entry_price or 50000.0, regime=regime,
        available_usdt=available, daily_pnl=daily_pnl,
        daily_pnl_pct=daily_pnl_pct, atr=atr,
        review_rejected=review_rejected,
    )


def test_hold_passes_immediately(session, profile):
    p = DecisionProposal(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        action="HOLD", confidence=0.0,
        strategy_mode="ai_observation", source="ai_trader",
    )
    r = _check(session, profile, p)
    assert r.result == "PASS"


def test_pass_on_clean_open_long(session, profile):
    r = _check(session, profile, _open_long())
    assert r.result == "PASS"


def test_daily_loss_circuit_breaker(session, profile):
    r = _check(session, profile, _open_long(), daily_pnl_pct=-0.04)
    assert r.result == "REJECT"
    assert "daily_loss" in r.reason


def test_consecutive_losses_circuit_breaker(session, profile):
    """3 连亏 → 拒。今天的 trades 全负."""
    for i in range(3):
        session.add(Trade(
            account_id=1, trading_mode="testnet",
            position_id=i + 1, symbol="BTCUSDT", side="LONG",
            entry_price=50000, exit_price=49000,
            quantity=0.01, pnl=-10.0, pnl_pct=-0.01,
            opened_at=datetime.now(tz=timezone.utc),
            closed_at=datetime.now(tz=timezone.utc),
            exit_reason="stop_loss",
        ))
    session.flush()
    r = _check(session, profile, _open_long())
    assert r.result == "REJECT"
    assert "consecutive_losses" in r.reason


def test_insufficient_balance(session, profile):
    r = _check(session, profile, _open_long(), available=0.0)
    assert r.result == "REJECT"
    assert "insufficient_balance" in r.reason


def test_already_open_position(session, profile):
    session.add(Position(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.01, entry_price=50000.0, stop_loss=49000.0,
        opened_at=datetime.now(tz=timezone.utc),
    ))
    session.flush()
    r = _check(session, profile, _open_long())
    assert r.result == "REJECT"
    assert "already_open" in r.reason


def test_oversize_position(session, profile):
    r = _check(session, profile, _open_long(size=0.30))
    assert r.result == "REJECT"
    assert "oversize" in r.reason


def test_single_risk_violation(session, profile):
    # SL 距离 1000 (大风险), size 0.1 → risk_pct = 1000/50000 * 0.1 = 0.002 = 0.2%
    # max_single = 0.01 = 1%, 这个不会触发, 改用更极端: SL 距离 6000 太远
    # 先看 SL 距离: ATR=200, max_mult=5 → max=1000. 6000 会先触发 sl_distance_out_of_range
    # 用 size=0.2 + sl 距离 600 → risk=600/50000*0.2=0.0024<0.01, 不触发
    # 真触发: size=0.20 + sl 距 1000 → risk=1000/50000*0.20=0.004 还不够
    # size=0.20 + sl 距 1000 ATR=200 (sl_mult=5 边界) → risk=0.004
    # 改: size=0.10, 但 max_single=0.01 = 1% → entry=50000, 把 SL 拉到 4000 距 → risk=4000/50000*0.1=0.008<1% 还不够
    # 把 max_single 改 0.001 (0.1%) 临时降低阈值, 让单笔风险更容易触发
    profile.max_single_risk_pct = Decimal("0.001")
    r = _check(session, profile, _open_long(entry=50000, sl=49500, tp=51500), atr=200.0)
    # SL 距 500, ATR=200 → SL 在 [100,1000] 内 OK; risk=500/50000*0.1=0.001 边界; 改 0.0009 阈值
    # 简化: 用更小阈值 0.0001 → risk=0.001 > 0.0001 触发
    profile.max_single_risk_pct = Decimal("0.0001")
    r = _check(session, profile, _open_long(entry=50000, sl=49500, tp=51500), atr=200.0)
    assert r.result == "REJECT"
    assert "single_risk" in r.reason


def test_sl_too_close_rejected(session, profile):
    # SL 距离 50, ATR 200, min_mult=0.5 → 最小 100, 50 < 100 触发
    r = _check(session, profile, _open_long(entry=50000, sl=49950, tp=50500), atr=200.0)
    assert r.result == "REJECT"
    assert "sl_distance" in r.reason


def test_sl_too_far_rejected(session, profile):
    # SL 距离 1500, ATR 200, max_mult=5 → 最大 1000, 1500 > 1000 触发
    r = _check(session, profile, _open_long(entry=50000, sl=48500, tp=53000), atr=200.0)
    assert r.result == "REJECT"
    assert "sl_distance" in r.reason


def test_poor_rr_rejected(session, profile):
    # SL 距 200 (1×ATR, 合理), TP 距 100 → R/R = 0.5 < 1.5
    r = _check(session, profile, _open_long(entry=50000, sl=49800, tp=50100), atr=200.0)
    assert r.result == "REJECT"
    assert "poor_rr" in r.reason


def test_chaotic_open_long_degrades(session, profile):
    r = _check(session, profile, _open_long(), regime="chaotic")
    assert r.result == "DEGRADE"
    assert r.modified_action == "HOLD"


def test_review_rejected_short_circuits(session, profile):
    r = _check(session, profile, _open_long(), review_rejected=True)
    assert r.result == "REJECT"
    assert "review_rejected" in r.reason


def test_every_call_writes_risk_event_audit(session, profile):
    _check(session, profile, _open_long())  # PASS
    rows = session.execute(select(RiskEvent)).scalars().all()
    assert len(rows) == 1
    assert rows[0].event_type == "GUARD_PASS"


# ---------------------------------------------------------------------------
# Plan 5 codereview I11: Guard 在 DEGRADE / REJECT 时 publish 事件
# ---------------------------------------------------------------------------

def _check_with_outbox(
    session, profile, proposal, *,
    regime="trending_up", available=10_000.0, daily_pnl=0.0, daily_pnl_pct=0.0,
    atr=200.0, decision_id=42, review_rejected=False,
):
    from src.events.outbox import OutboxWriter
    g = ExecutionGuard(session, risk_profile=profile, outbox=OutboxWriter())
    return g.check(
        proposal=proposal, trading_mode="testnet",
        current_price=proposal.entry_price or 50000.0, regime=regime,
        available_usdt=available, daily_pnl=daily_pnl,
        daily_pnl_pct=daily_pnl_pct, atr=atr,
        review_rejected=review_rejected,
        decision_id=decision_id, trace_id="t-test",
    )


def test_pass_does_not_publish_decision_event(session, profile):
    from src.models.event_store import EventOutbox
    _check_with_outbox(session, profile, _open_long())  # PASS
    rows = session.execute(select(EventOutbox)).scalars().all()
    assert rows == []  # PASS 不发 decision.* 事件


def test_degrade_publishes_decision_degraded(session, profile):
    from src.models.event_store import EventOutbox
    r = _check_with_outbox(
        session, profile, _open_long(), regime="chaotic",
    )
    assert r.result == "DEGRADE"
    rows = session.execute(select(EventOutbox)).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.event_type == "decision.degraded"
    assert row.aggregate_id == 42
    payload = row.payload_json["payload"]
    assert payload["decision_id"] == 42
    assert payload["original_action"] == "OPEN_LONG"
    assert payload["modified_action"] == "HOLD"
    assert "chaotic" in payload["reason"]


def test_reject_publishes_decision_rejected(session, profile):
    from src.models.event_store import EventOutbox
    r = _check_with_outbox(
        session, profile, _open_long(), daily_pnl_pct=-0.04,
    )
    assert r.result == "REJECT"
    rows = session.execute(
        select(EventOutbox).where(EventOutbox.event_type == "decision.rejected")
    ).scalars().all()
    assert len(rows) == 1
    payload = rows[0].payload_json["payload"]
    assert payload["decision_id"] == 42
    assert "daily_loss" in payload["reason"]


def test_no_decision_id_skips_publish(session, profile):
    """decision_id=None 时不应 publish (没有 ai_decisions 行可关联)."""
    from src.models.event_store import EventOutbox
    _check_with_outbox(
        session, profile, _open_long(), regime="chaotic", decision_id=None,
    )
    rows = session.execute(select(EventOutbox)).scalars().all()
    assert rows == []


def test_no_outbox_no_publish(session, profile):
    """不注入 outbox 时, 行为与原版一致 — 只写 risk_events, 不发事件."""
    from src.models.event_store import EventOutbox
    _check(session, profile, _open_long(), regime="chaotic")  # 默认无 outbox
    rows = session.execute(select(EventOutbox)).scalars().all()
    assert rows == []
