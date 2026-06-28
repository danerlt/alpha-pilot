"""GET/POST /api/attribution 集成测试 (PRD 8.1.3)。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.db.session import get_db
from src.models import Base
from src.models.trade import Trade

_NOW = datetime.now(timezone.utc)


@pytest.fixture
def client():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)

    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override

    from types import SimpleNamespace

    from src.controllers.dependencies import get_current_user, require_admin

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role="user")
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id=1, role="admin")
    yield TestClient(app), engine
    app.dependency_overrides.clear()


def _add_trade(s, *, symbol="BTCUSDT", pnl=10.0, exit_reason="take_profit", regime="trending_up"):
    s.add(Trade(
        account_id=1, trading_mode="testnet", position_id=1, symbol=symbol, side="LONG",
        quantity=0.1, entry_price=100.0, exit_price=100.0 + pnl, pnl=pnl, pnl_pct=0.02,
        exit_reason=exit_reason, strategy_mode="breakout", regime=regime,
        opened_at=_NOW - timedelta(days=1, hours=1), closed_at=_NOW - timedelta(days=1),
        holding_seconds=3600,
    ))


def test_generate_then_list_and_summary(client):
    cli, engine = client
    with Session(engine) as s:
        _add_trade(s, symbol="BTCUSDT", pnl=10.0, exit_reason="take_profit")
        _add_trade(s, symbol="BTCUSDT", pnl=-4.0, exit_reason="stop_loss")
        _add_trade(s, symbol="ETHUSDT", pnl=6.0, exit_reason="ai_close")
        s.commit()

    gen = cli.post("/api/attribution/generate?window_days=30")
    assert gen.status_code == 200
    assert gen.json()["data"]["trades"] == 3

    listed = cli.get("/api/attribution").json()["data"]
    assert len(listed) == 3
    assert all(row["narrative"] for row in listed)

    summary = cli.get("/api/attribution/summary?window_days=30").json()["data"]
    assert summary["total_trades"] == 3
    assert abs(summary["total_pnl"] - 12.0) < 1e-9
    by_sym = {b["key"]: b for b in summary["by_symbol"]}
    assert abs(by_sym["BTCUSDT"]["pnl_sum"] - 6.0) < 1e-9


def test_summary_empty(client):
    cli, _ = client
    r = cli.get("/api/attribution/summary")
    assert r.status_code == 200
    assert r.json()["data"]["total_trades"] == 0
