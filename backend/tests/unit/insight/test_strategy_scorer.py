"""阶段2+3: strategy_score crud upsert + StrategyScorer 分组聚合 (真 PG)。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.cruds.strategy_score_crud import strategy_score_crud
from src.models.trade import Trade
from src.services.insight.scoring.scorer import StrategyScorer

_NOW = datetime.now(timezone.utc)


def _add_trade(session, *, symbol, strategy_mode, regime, pnl, pnl_pct, exit_reason, days_ago=1):
    t = Trade(
        account_id=1, trading_mode="testnet", position_id=1, symbol=symbol,
        side="LONG", quantity=0.1, entry_price=100.0, exit_price=100.0 + pnl,
        pnl=pnl, pnl_pct=pnl_pct, exit_reason=exit_reason,
        strategy_mode=strategy_mode, regime=regime,
        opened_at=_NOW - timedelta(days=days_ago, hours=1),
        closed_at=_NOW - timedelta(days=days_ago),
    )
    session.add(t)
    return t


def test_upsert_score_is_idempotent_by_key(pg_session):
    key = dict(account_id=1, strategy_mode="breakout", symbol="BTCUSDT", regime="trending_up", window="30d")
    strategy_score_crud.upsert_score(
        pg_session, **key, win_rate=0.5, pnl_sum=10.0, max_drawdown=None,
        sharpe=None, false_breakout_rate=0.2, regime_fit_score=None, sample_count=4,
    )
    pg_session.commit()
    # 同 key 再 upsert → 更新而非新增
    strategy_score_crud.upsert_score(
        pg_session, **key, win_rate=0.75, pnl_sum=20.0, max_drawdown=-3.0,
        sharpe=1.2, false_breakout_rate=0.1, regime_fit_score=None, sample_count=8,
    )
    pg_session.commit()

    rows = strategy_score_crud.find_by_window(pg_session, account_id=1, window="30d")
    matching = [r for r in rows if r.strategy_mode == "breakout" and r.symbol == "BTCUSDT"]
    assert len(matching) == 1
    assert float(matching[0].win_rate) == 0.75
    assert matching[0].sample_count == 8


def test_scorer_groups_by_strategy_symbol_regime(pg_session):
    # breakout/BTCUSDT/trending_up: 2 笔 (1 胜 1 止损)
    _add_trade(pg_session, symbol="BTCUSDT", strategy_mode="breakout", regime="trending_up",
               pnl=10.0, pnl_pct=0.02, exit_reason="take_profit")
    _add_trade(pg_session, symbol="BTCUSDT", strategy_mode="breakout", regime="trending_up",
               pnl=-5.0, pnl_pct=-0.01, exit_reason="stop_loss")
    # trend_following/ETHUSDT/ranging: 1 笔
    _add_trade(pg_session, symbol="ETHUSDT", strategy_mode="trend_following", regime="ranging",
               pnl=3.0, pnl_pct=0.006, exit_reason="ai_close")
    pg_session.commit()

    scorer = StrategyScorer(pg_session, account_id=1)
    n = scorer.score_window(trading_mode="testnet", window="30d", window_days=30)
    pg_session.commit()
    assert n == 2  # 两个维度组合

    rows = strategy_score_crud.find_by_window(pg_session, account_id=1, window="30d")
    by_key = {(r.strategy_mode, r.symbol, r.regime): r for r in rows}

    bt = by_key[("breakout", "BTCUSDT", "trending_up")]
    assert bt.sample_count == 2
    assert abs(float(bt.win_rate) - 0.5) < 1e-9
    assert abs(float(bt.pnl_sum) - 5.0) < 1e-9
    assert abs(float(bt.false_breakout_rate) - 0.5) < 1e-9  # 1/2 止损退出

    et = by_key[("trend_following", "ETHUSDT", "ranging")]
    assert et.sample_count == 1


def test_scorer_uses_unknown_for_null_dimensions(pg_session):
    _add_trade(pg_session, symbol="BTCUSDT", strategy_mode=None, regime=None,
               pnl=1.0, pnl_pct=0.002, exit_reason="ai_close")
    pg_session.commit()

    StrategyScorer(pg_session, account_id=1).score_window(trading_mode="testnet")
    pg_session.commit()

    rows = strategy_score_crud.find_by_window(pg_session, account_id=1, window="30d")
    row = [r for r in rows if r.symbol == "BTCUSDT" and r.strategy_mode == "unknown"][0]
    assert row.regime == "unknown"


def test_scorer_isolates_trading_mode(pg_session):
    _add_trade(pg_session, symbol="BTCUSDT", strategy_mode="breakout", regime="trending_up",
               pnl=10.0, pnl_pct=0.02, exit_reason="take_profit")
    pg_session.commit()
    # mainnet 评分窗口应查不到 testnet 的交易
    n = StrategyScorer(pg_session, account_id=1).score_window(trading_mode="mainnet")
    pg_session.commit()
    assert n == 0
