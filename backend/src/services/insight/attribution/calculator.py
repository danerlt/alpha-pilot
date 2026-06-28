"""交易归因纯计算 (PRD 8.1.3 + 12.1)。

- time_bucket(dt): UTC 小时分 4 时段 (night/morning/afternoon/evening)。
- build_trade_narrative(trade): 逐笔中文可解释叙述。
- compute_attribution_summary(trades): 按 symbol/exit_reason/regime/time_bucket 拆解盈亏。

无状态纯函数, duck-typed 输入。
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

_EXIT_REASON_ZH = {
    "stop_loss": "止损",
    "take_profit": "止盈",
    "ai_close": "AI 平仓",
    "manual_close": "手动平仓",
    "circuit_breaker": "熔断平仓",
    "partial": "部分平仓",
}


def time_bucket(dt: datetime) -> str:
    """按 UTC 小时分 4 时段。"""
    h = dt.hour
    if h < 6:
        return "night"
    if h < 12:
        return "morning"
    if h < 18:
        return "afternoon"
    return "evening"


def _exit_reason_zh(reason: str) -> str:
    return _EXIT_REASON_ZH.get(reason, reason)


def build_trade_narrative(trade) -> str:
    """逐笔中文叙述: 标的 + 行情 + 策略 + 退出原因 + 盈亏 + 持仓时长。"""
    pnl = float(trade.pnl)
    pct = float(trade.pnl_pct) * 100
    regime = trade.regime or "unknown"
    strategy = trade.strategy_mode or "unknown"
    reason = _exit_reason_zh(trade.exit_reason)
    holding = trade.holding_seconds
    hold_str = f"，持仓 {holding // 3600}h{(holding % 3600) // 60}m" if holding else ""
    outcome = "盈利" if pnl >= 0 else "亏损"
    sign = "+" if pnl >= 0 else ""
    return (
        f"{trade.symbol} 在 {regime} 行情下，{strategy} 策略{reason}，"
        f"{outcome} {sign}{pnl} ({sign}{pct:.2f}%){hold_str}。"
    )


@dataclass(frozen=True)
class AttributionSummary:
    total_trades: int
    total_pnl: float
    by_symbol: list[dict] = field(default_factory=list)
    by_exit_reason: list[dict] = field(default_factory=list)
    by_regime: list[dict] = field(default_factory=list)
    by_time_bucket: list[dict] = field(default_factory=list)


def _breakdown(trades: Sequence[object], key_fn) -> list[dict]:
    """按 key_fn 分组, 算每组 pnl_sum/trade_count/win_rate, 按 pnl_sum 降序。"""
    buckets: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        buckets[key_fn(t)].append(float(t.pnl))
    rows = []
    for key, pnls in buckets.items():
        count = len(pnls)
        wins = sum(1 for p in pnls if p > 0)
        rows.append({
            "key": key,
            "pnl_sum": sum(pnls),
            "trade_count": count,
            "win_rate": wins / count if count else None,
        })
    rows.sort(key=lambda r: r["pnl_sum"], reverse=True)
    return rows


def compute_attribution_summary(trades: Sequence[object]) -> AttributionSummary:
    if not trades:
        return AttributionSummary(total_trades=0, total_pnl=0.0)
    return AttributionSummary(
        total_trades=len(trades),
        total_pnl=sum(float(t.pnl) for t in trades),
        by_symbol=_breakdown(trades, lambda t: t.symbol),
        by_exit_reason=_breakdown(trades, lambda t: t.exit_reason),
        by_regime=_breakdown(trades, lambda t: t.regime or "unknown"),
        by_time_bucket=_breakdown(trades, lambda t: time_bucket(t.closed_at)),
    )
