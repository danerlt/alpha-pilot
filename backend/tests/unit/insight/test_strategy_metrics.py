"""阶段1: compute_strategy_metrics 纯计算单测 (duck-typed 假 trade, 不碰 DB)。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from src.services.insight.scoring.metrics import StrategyMetrics, compute_strategy_metrics

_T0 = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _trade(pnl: float, pnl_pct: float, exit_reason: str = "take_profit", minutes: int = 0):
    return SimpleNamespace(
        pnl=pnl, pnl_pct=pnl_pct, exit_reason=exit_reason,
        closed_at=_T0 + timedelta(minutes=minutes),
    )


def test_empty_returns_zero_metrics():
    m = compute_strategy_metrics([])
    assert isinstance(m, StrategyMetrics)
    assert m.total_trades == 0
    assert m.winning_trades == 0
    assert m.win_rate is None
    assert m.total_pnl == 0.0
    assert m.avg_pnl_pct is None
    assert m.max_drawdown is None
    assert m.sharpe is None
    assert m.stop_loss_exit_rate is None


def test_win_rate_and_totals():
    trades = [
        _trade(10.0, 0.02),
        _trade(-5.0, -0.01, exit_reason="stop_loss"),
        _trade(8.0, 0.015),
    ]
    m = compute_strategy_metrics(trades)
    assert m.total_trades == 3
    assert m.winning_trades == 2
    assert abs(m.win_rate - 2 / 3) < 1e-9
    assert abs(m.total_pnl - 13.0) < 1e-9
    assert abs(m.avg_pnl_pct - (0.02 - 0.01 + 0.015) / 3) < 1e-9


def test_stop_loss_exit_rate():
    trades = [
        _trade(-5.0, -0.01, exit_reason="stop_loss"),
        _trade(-3.0, -0.006, exit_reason="stop_loss"),
        _trade(10.0, 0.02, exit_reason="take_profit"),
        _trade(2.0, 0.004, exit_reason="ai_close"),
    ]
    m = compute_strategy_metrics(trades)
    assert abs(m.stop_loss_exit_rate - 0.5) < 1e-9


def test_max_drawdown_tracks_cumulative_peak():
    # 累计: +10 → +4(-6 回撤) → +14 → +9(-5 回撤). 最大回撤 = -6
    trades = [
        _trade(10.0, 0.02, minutes=0),
        _trade(-6.0, -0.012, exit_reason="stop_loss", minutes=1),
        _trade(10.0, 0.02, minutes=2),
        _trade(-5.0, -0.01, exit_reason="stop_loss", minutes=3),
    ]
    m = compute_strategy_metrics(trades)
    assert m.max_drawdown is not None
    assert abs(m.max_drawdown - (-6.0)) < 1e-9


def test_max_drawdown_none_when_monotonic_up():
    trades = [_trade(5.0, 0.01, minutes=0), _trade(3.0, 0.006, minutes=1)]
    m = compute_strategy_metrics(trades)
    assert m.max_drawdown is None  # 单调上升无回撤


def test_sharpe_needs_at_least_two_trades():
    assert compute_strategy_metrics([_trade(10.0, 0.02)]).sharpe is None


def test_sharpe_none_when_zero_variance():
    # 所有 pnl_pct 相同 → std=0 → sharpe None (避免除零)
    trades = [_trade(5.0, 0.01), _trade(5.0, 0.01), _trade(5.0, 0.01)]
    assert compute_strategy_metrics(trades).sharpe is None


def test_sharpe_positive_for_net_winning_series():
    trades = [_trade(10.0, 0.02), _trade(-2.0, -0.004), _trade(8.0, 0.016)]
    m = compute_strategy_metrics(trades)
    assert m.sharpe is not None
    assert m.sharpe > 0  # 正收益均值 → 正夏普
