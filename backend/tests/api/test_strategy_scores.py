"""GET/POST /api/strategy-scores 集成测试 (PRD 8.2.5)。"""
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
from src.models.attribution import StrategyScore
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

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role="user", status="active",
    )
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", status="active",
    )
    yield TestClient(app), engine
    app.dependency_overrides.clear()


def test_list_strategy_scores_returns_rows(client):
    cli, engine = client
    with Session(engine) as s:
        s.add(StrategyScore(
            account_id=1, strategy_mode="breakout", symbol="BTCUSDT", regime="trending_up",
            window="30d", win_rate=0.6, pnl_sum=12.0, max_drawdown=-3.0, sharpe=1.1,
            false_breakout_rate=0.25, regime_fit_score=None, sample_count=5,
        ))
        s.commit()

    r = cli.get("/api/strategy-scores?window=30d")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["strategy_mode"] == "breakout"
    assert data[0]["win_rate"] == 0.6
    assert data[0]["sample_count"] == 5


def test_generate_strategy_scores_admin(client):
    cli, engine = client
    with Session(engine) as s:
        s.add(Trade(
            account_id=1, trading_mode="testnet", position_id=1, symbol="BTCUSDT",
            side="LONG", quantity=0.1, entry_price=100.0, exit_price=110.0,
            pnl=10.0, pnl_pct=0.02, exit_reason="take_profit",
            strategy_mode="breakout", regime="trending_up",
            opened_at=_NOW - timedelta(days=1, hours=1), closed_at=_NOW - timedelta(days=1),
        ))
        s.commit()

    r = cli.post("/api/strategy-scores/generate?window_days=30")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["groups"] == 1
    assert data["window"] == "30d"

    # 评分结果可查
    listed = cli.get("/api/strategy-scores?window=30d").json()["data"]
    assert any(row["symbol"] == "BTCUSDT" for row in listed)


def test_list_empty_window_returns_empty(client):
    cli, _ = client
    r = cli.get("/api/strategy-scores?window=7d")
    assert r.status_code == 200
    assert r.json()["data"] == []
