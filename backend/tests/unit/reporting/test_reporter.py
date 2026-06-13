"""generate_daily_report 单测 (TEST-4 补强) — 真 PG。

覆盖: 胜负统计 / total_pnl / win_rate / max_single_loss / upsert 幂等 / 空交易日。
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.models.trade import Trade
from src.services.reporting.reporter import generate_daily_report


def _trade(pnl: float, *, symbol: str = "BTCUSDT", reason: str = "take_profit") -> Trade:
    now = datetime.now(timezone.utc)
    return Trade(
        account_id=1, trading_mode="testnet", position_id=1, symbol=symbol,
        side="LONG", quantity=0.01, entry_price=50_000.0, exit_price=50_500.0,
        pnl=pnl, pnl_pct=pnl / 500.0, exit_reason=reason,
        opened_at=now, closed_at=now, holding_seconds=3600,
    )


@pytest.mark.asyncio
async def test_report_aggregates_wins_losses_and_pnl(pg_session):
    pg_session.add_all([_trade(10.0), _trade(5.0), _trade(-8.0, reason="stop_loss")])
    pg_session.commit()

    report = generate_daily_report(pg_session, report_date=date.today())

    assert report.total_trades == 3
    assert report.winning_trades == 2
    assert report.losing_trades == 1
    assert float(report.total_pnl) == pytest.approx(7.0)
    assert float(report.win_rate) == pytest.approx(2 / 3, abs=1e-4)  # Numeric(10,6) 存储舍入
    assert float(report.max_single_loss) == pytest.approx(-8.0)
    assert report.risk_events_count == 0
    assert set(report.summary["symbols_traded"]) == {"BTCUSDT"}
    assert report.summary["exit_reasons"] == {"take_profit": 2, "stop_loss": 1}


@pytest.mark.asyncio
async def test_report_empty_day_has_no_winrate(pg_session):
    report = generate_daily_report(pg_session, report_date=date.today())
    assert report.total_trades == 0
    assert report.win_rate is None
    assert report.max_single_loss is None
    assert float(report.total_pnl) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_report_upsert_is_idempotent(pg_session):
    pg_session.add(_trade(10.0))
    pg_session.commit()
    r1 = generate_daily_report(pg_session, report_date=date.today())
    rid = r1.id

    # 再加一笔后重算 — 同一行被 upsert, 不新增
    pg_session.add(_trade(20.0))
    pg_session.commit()
    r2 = generate_daily_report(pg_session, report_date=date.today())

    assert r2.id == rid  # 同一行
    assert r2.total_trades == 2
    assert float(r2.total_pnl) == pytest.approx(30.0)
