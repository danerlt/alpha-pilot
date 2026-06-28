"""阶段2: TradeAttribution crud upsert + AttributionService (真 PG)。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.cruds.trade_attribution_crud import trade_attribution_crud
from src.models.trade import Trade
from src.services.insight.attribution.service import AttributionService

_NOW = datetime.now(timezone.utc)


def _add_trade(session, *, symbol="BTCUSDT", pnl=10.0, pnl_pct=0.02,
               exit_reason="take_profit", regime="trending_up", strategy_mode="breakout",
               trading_mode="testnet", days_ago=1):
    t = Trade(
        account_id=1, trading_mode=trading_mode, position_id=1, symbol=symbol,
        side="LONG", quantity=0.1, entry_price=100.0, exit_price=100.0 + pnl,
        pnl=pnl, pnl_pct=pnl_pct, exit_reason=exit_reason,
        strategy_mode=strategy_mode, regime=regime,
        opened_at=_NOW - timedelta(days=days_ago, hours=1),
        closed_at=_NOW - timedelta(days=days_ago), holding_seconds=3600,
    )
    session.add(t)
    session.flush()
    return t


def test_upsert_for_trade_idempotent(pg_session):
    t = _add_trade(pg_session)
    pg_session.commit()
    trade_attribution_crud.upsert_for_trade(
        pg_session, trade_id=t.id, by_symbol={"symbol": "BTCUSDT", "pnl": 10.0},
        by_time_bucket="afternoon", by_exit_reason="take_profit", narrative="v1",
    )
    pg_session.commit()
    trade_attribution_crud.upsert_for_trade(
        pg_session, trade_id=t.id, by_symbol={"symbol": "BTCUSDT", "pnl": 10.0},
        by_time_bucket="afternoon", by_exit_reason="take_profit", narrative="v2",
    )
    pg_session.commit()

    rows = trade_attribution_crud.list_recent(pg_session, limit=100)
    matching = [r for r in rows if r.trade_id == t.id]
    assert len(matching) == 1
    assert matching[0].narrative == "v2"


def test_attribute_window_writes_per_trade_and_returns_summary(pg_session):
    _add_trade(pg_session, symbol="BTCUSDT", pnl=10.0, exit_reason="take_profit")
    _add_trade(pg_session, symbol="BTCUSDT", pnl=-4.0, exit_reason="stop_loss")
    _add_trade(pg_session, symbol="ETHUSDT", pnl=6.0, exit_reason="ai_close")
    pg_session.commit()

    summary = AttributionService(pg_session).attribute_window(trading_mode="testnet")
    pg_session.commit()

    assert summary.total_trades == 3
    assert abs(summary.total_pnl - 12.0) < 1e-9
    by_sym = {b["key"]: b for b in summary.by_symbol}
    assert abs(by_sym["BTCUSDT"]["pnl_sum"] - 6.0) < 1e-9

    # 逐笔归因已写表且含叙述
    rows = trade_attribution_crud.list_recent(pg_session, limit=100)
    assert len([r for r in rows if r.narrative]) >= 3
    assert any("BTCUSDT" in (r.narrative or "") for r in rows)


def test_attribute_window_isolates_trading_mode(pg_session):
    _add_trade(pg_session, trading_mode="testnet", pnl=10.0)
    pg_session.commit()
    summary = AttributionService(pg_session).summary_only(trading_mode="mainnet")
    assert summary.total_trades == 0
