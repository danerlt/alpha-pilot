"""策略评分指标纯计算 (PRD 8.2.5)。

compute_strategy_metrics(trades) 对一组已平仓交易聚合出评分维度;
无状态纯函数, duck-typed 输入 (只读 t.pnl / t.pnl_pct / t.exit_reason / t.closed_at)。
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Sequence

_STOP_LOSS_REASON = "stop_loss"


@dataclass(frozen=True)
class StrategyMetrics:
    total_trades: int
    winning_trades: int
    win_rate: float | None          # wins/total; 无交易 None
    total_pnl: float
    avg_pnl_pct: float | None       # mean(pnl_pct); 无交易 None
    max_drawdown: float | None      # 累计 PnL 曲线最大回撤 (≤0); 无回撤 None
    sharpe: float | None            # mean(pnl_pct)/stdev(pnl_pct); <2 笔或零方差 None
    stop_loss_exit_rate: float | None  # 止损退出占比; 无交易 None


def _max_drawdown(sorted_pnls: list[float]) -> float | None:
    cumulative = 0.0
    peak = 0.0
    min_dd = 0.0
    for pnl in sorted_pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = cumulative - peak
        if dd < min_dd:
            min_dd = dd
    return min_dd if min_dd < 0 else None


def compute_strategy_metrics(trades: Sequence[object]) -> StrategyMetrics:
    total = len(trades)
    if total == 0:
        return StrategyMetrics(
            total_trades=0, winning_trades=0, win_rate=None,
            total_pnl=0.0, avg_pnl_pct=None, max_drawdown=None,
            sharpe=None, stop_loss_exit_rate=None,
        )

    pnls = [float(t.pnl) for t in trades]
    pcts = [float(t.pnl_pct) for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    total_pnl = sum(pnls)
    stop_losses = sum(1 for t in trades if t.exit_reason == _STOP_LOSS_REASON)

    # max drawdown 按平仓时间排序后算累计回撤
    ordered = sorted(trades, key=lambda t: t.closed_at)
    max_dd = _max_drawdown([float(t.pnl) for t in ordered])

    # sharpe: 需 ≥2 笔且方差非零
    sharpe: float | None = None
    if total >= 2:
        std = statistics.stdev(pcts)
        if std > 0:
            sharpe = statistics.fmean(pcts) / std

    return StrategyMetrics(
        total_trades=total,
        winning_trades=wins,
        win_rate=wins / total,
        total_pnl=total_pnl,
        avg_pnl_pct=statistics.fmean(pcts),
        max_drawdown=max_dd,
        sharpe=sharpe,
        stop_loss_exit_rate=stop_losses / total,
    )
