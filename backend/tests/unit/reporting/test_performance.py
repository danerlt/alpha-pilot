"""PerformanceService 对账测试 (roadmap P6 验收: 指标与 DB 交易记录一致)。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.common.exception.errors import ParamsException
from src.models import Base
from src.models.account import AccountSnapshot
from src.models.trade import Trade
from src.services.reporting.performance import PerformanceService, _max_drawdown


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _trade(session, *, pnl, closed_at, symbol="BTCUSDT", strategy="ai_trend", exit_reason="take_profit", holding=3600):
    session.add(Trade(
        account_id=1, trading_mode="testnet", position_id=1,
        symbol=symbol, side="LONG", quantity=0.01,
        entry_price=50_000, exit_price=50_000 + pnl * 1000,
        pnl=pnl, pnl_pct=pnl / 500, exit_reason=exit_reason,
        strategy_mode=strategy,
        opened_at=closed_at - timedelta(seconds=holding), closed_at=closed_at,
        holding_seconds=holding,
    ))


def _seed(session):
    now = datetime.now(tz=timezone.utc)
    # 3 笔: +100, +50, -50 → win_rate 2/3, profit_factor 150/50=3
    _trade(session, pnl=100.0, closed_at=now - timedelta(days=1))
    _trade(session, pnl=50.0, closed_at=now - timedelta(days=10), symbol="ETHUSDT", strategy="ai_breakout")
    _trade(session, pnl=-50.0, closed_at=now - timedelta(days=40), exit_reason="stop_loss")
    # 权益曲线: 10000 → 10100 (两天)
    session.add(AccountSnapshot(
        account_id=1, trading_mode="testnet", snapshot_at=now - timedelta(days=2),
        total_balance_usdt=10_000, available_balance_usdt=10_000,
        unrealized_pnl=0, daily_pnl=0, daily_pnl_pct=0,
    ))
    session.add(AccountSnapshot(
        account_id=1, trading_mode="testnet", snapshot_at=now,
        total_balance_usdt=10_100, available_balance_usdt=10_100,
        unrealized_pnl=0, daily_pnl=100, daily_pnl_pct=0.0099,
    ))
    session.commit()


def test_summary_reconciles_with_trades(session):
    _seed(session)
    out = PerformanceService(session).summary(trading_mode="testnet", range_days=90)
    assert out["trades"] == 3
    assert out["net_pnl"] == pytest.approx(100.0)
    assert out["win_rate"] == pytest.approx(2 / 3, abs=1e-4)
    assert out["profit_factor"] == pytest.approx(3.0)
    assert out["net_return_pct"] == pytest.approx(0.01)  # 10000→10100
    assert out["today_trades"] == 0
    assert out["week_pnl"] == pytest.approx(100.0)   # 近 7 天只有 +100
    assert out["month_pnl"] == pytest.approx(150.0)  # 近 30 天 +100+50
    assert out["avg_holding_seconds"] == 3600
    assert isinstance(out["curve"], list) and len(out["curve"]) == 2


def test_monthly_buckets_reconcile(session):
    _seed(session)
    rows = PerformanceService(session).monthly(trading_mode="testnet", months=3)
    assert sum(r["pnl"] for r in rows) == pytest.approx(100.0)
    assert sum(r["trades"] for r in rows) == 3


@pytest.mark.parametrize("dim,expect_keys", [
    ("symbol", {"BTCUSDT", "ETHUSDT"}),
    ("strategy", {"ai_trend", "ai_breakout"}),
    ("trigger", {"take_profit", "stop_loss"}),
])
def test_attribution_dims(session, dim, expect_keys):
    _seed(session)
    rows = PerformanceService(session).attribution(trading_mode="testnet", dim=dim)
    assert {r["key"] for r in rows} == expect_keys
    assert sum(r["net_pnl"] for r in rows) == pytest.approx(100.0)
    # 排序: 净收益降序
    assert rows[0]["net_pnl"] >= rows[-1]["net_pnl"]


def test_attribution_rejects_bad_dim(session):
    with pytest.raises(ParamsException):
        PerformanceService(session).attribution(trading_mode="testnet", dim="hacker")


def test_max_drawdown():
    assert _max_drawdown([100, 120, 90, 110, 80]) == pytest.approx(-1 / 3)
    assert _max_drawdown([100, 110, 120]) == 0.0
