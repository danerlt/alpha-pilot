"""webapp 联调缺口收口测试 (docs/webapp联调-后端待办.md #1-4,6,7)。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.common.enums import PositionStatus
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.models import Base
from src.models.account import AccountSnapshot
from src.models.account_entity import RiskProfile
from src.models.decision import AIDecision
from src.models.order import Order
from src.models.position import Position
from src.models.risk_event import RiskEvent


@pytest.fixture
def authed(monkeypatch):
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)

    def _override():
        s = Session(eng)
        try:
            yield s
        finally:
            s.close()

    from types import SimpleNamespace

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role="user", status="active",
    )
    yield TestClient(app), eng
    app.dependency_overrides.clear()


def test_gap1_decision_list_carries_guard_verdict(authed):
    cli, eng = authed
    now = datetime.now(tz=timezone.utc)
    with Session(eng) as s:
        d = AIDecision(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
            decided_at=now, action="OPEN_LONG", confidence=0.7, is_fallback=False,
        )
        s.add(d)
        s.flush()
        s.add(RiskEvent(
            account_id=1, trading_mode="testnet", event_type="GUARD_REJECT",
            symbol="BTCUSDT", triggered_at=now, description="oversize",
            resolved=False, decision_id=d.id,
        ))
        s.commit()
    r = cli.get("/api/decisions")
    data = r.json()["data"]
    assert data[0]["guard_verdict"] == "REJECT"


def test_gap2_account_history_series(authed):
    cli, eng = authed
    base = datetime.now(tz=timezone.utc)
    with Session(eng) as s:
        for i in range(3):
            s.add(AccountSnapshot(
                account_id=1, trading_mode="testnet",
                snapshot_at=base + timedelta(minutes=i),
                total_balance_usdt=10_000 + i, available_balance_usdt=10_000,
                unrealized_pnl=0, daily_pnl=0, daily_pnl_pct=0,
            ))
        s.commit()
    r = cli.get("/api/account/history?limit=10")
    data = r.json()["data"]
    assert [p["equity"] for p in data] == [10_000.0, 10_001.0, 10_002.0]  # 时间正序
    assert set(data[0]) == {"ts", "equity"}


def test_gap3_orders_list(authed):
    cli, eng = authed
    now = datetime.now(tz=timezone.utc)
    with Session(eng) as s:
        s.add(Order(
            account_id=1, trading_mode="testnet", trace_id="t" * 32,
            symbol="BTCUSDT", side="BUY", order_type="MARKET",
            quantity=0.01, status="FILLED", submitted_at=now,
        ))
        s.commit()
    r = cli.get("/api/orders")
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["status"] == "FILLED"
    assert data[0]["trace_id"] == "t" * 32


def test_gap4_position_strategy_mode_and_pct(authed):
    cli, eng = authed
    now = datetime.now(tz=timezone.utc)
    with Session(eng) as s:
        d = AIDecision(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
            decided_at=now, action="OPEN_LONG", confidence=0.7,
            strategy_mode="ai_trend", is_fallback=False,
        )
        s.add(d)
        s.flush()
        s.add(AccountSnapshot(
            account_id=1, trading_mode="testnet", snapshot_at=now,
            total_balance_usdt=10_000, available_balance_usdt=9_000,
            unrealized_pnl=0, daily_pnl=0, daily_pnl_pct=0,
        ))
        s.add(Position(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT",
            status=PositionStatus.OPEN.value, side="LONG",
            quantity=0.02, entry_price=50_000.0, current_price=50_000.0,
            stop_loss=49_000.0, opened_at=now, ai_decision_id=d.id,
        ))
        s.commit()
    r = cli.get("/api/positions")
    row = r.json()["data"][0]
    assert row["strategy_mode"] == "ai_trend"
    assert row["position_pct"] == pytest.approx(0.1)  # 1000/10000


def test_gap7_risk_limits_view(authed):
    cli, eng = authed
    with Session(eng) as s:
        s.add(RiskProfile(
            account_id=1, name="default", version=1, active=True,
            max_position_size_pct=Decimal("0.20"),
            max_daily_loss_pct=Decimal("0.03"),
            max_consecutive_losses=3,
            max_single_risk_pct=Decimal("0.01"),
            min_rr_ratio=Decimal("1.50"),
            sl_atr_min_mult=Decimal("0.50"),
            sl_atr_max_mult=Decimal("5.00"),
        ))
        s.commit()
    r = cli.get("/api/risk/limits")
    data = r.json()["data"]
    assert data["max_daily_loss_pct"] == 0.03
    assert data["min_rr_ratio"] == 1.5


def test_gap6_catchup_typed_in_openapi():
    schema = app.openapi()
    components = schema.get("components", {}).get("schemas", {})
    assert "CatchupOut" in components


def test_gap5_performance_summary_endpoint(authed):
    """联调缺口#5: 主控台磁贴数据由 /api/performance/summary 提供。"""
    cli, _ = authed
    r = cli.get("/api/performance/summary?range=30")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    for key in ("sharpe", "win_rate", "today_trades", "week_pnl", "month_pnl", "curve"):
        assert key in data
