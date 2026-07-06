"""PerformanceService — 绩效归因三接口 (handoff 3.8) + 联调缺口#5 聚合指标。

数据源全部来自 DB (trades + account_snapshots + candles), 与交易记录可对账
(roadmap P6 验收)。Sharpe/Sortino 用权益曲线日收益率年化 (√365), 样本不足返 None。
HODL 基准: BTCUSDT 收盘价在同区间的归一化收益。
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.exception.errors import ParamsException
from src.models.account import AccountSnapshot
from src.models.candle import Candle
from src.models.trade import Trade

logger = logging.getLogger(__name__)

_ATTRIBUTION_DIMS = {"symbol", "strategy", "trigger"}
_HODL_SYMBOL = "BTCUSDT"
_CURVE_MAX_POINTS = 200


def _annualized_ratio(returns: list[float], *, downside_only: bool) -> float | None:
    """日收益率序列 → 年化 Sharpe/Sortino; 样本 <5 或分母为 0 返 None。"""
    if len(returns) < 5:
        return None
    mean = sum(returns) / len(returns)
    base = [r for r in returns if r < 0] if downside_only else returns
    if not base:
        return None
    var = sum((r - (0 if downside_only else mean)) ** 2 for r in base) / len(base)
    std = math.sqrt(var)
    if std == 0:
        return None
    return round(mean / std * math.sqrt(365), 4)


def _max_drawdown(equity: list[float]) -> float:
    peak = float("-inf")
    mdd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, (v - peak) / peak)
    return round(mdd, 6)


class PerformanceService:
    def __init__(self, session: Session):
        self._session = session

    # ── summary ─────────────────────────────────────────────────────────

    def summary(self, *, trading_mode: str, range_days: int = 90, account_id: int = 1) -> dict:
        now = datetime.now(tz=timezone.utc)
        since = now - timedelta(days=range_days)

        trades = list(self._session.execute(
            select(Trade).where(
                Trade.account_id == account_id,
                Trade.trading_mode == trading_mode,
                Trade.closed_at >= since,
            ).order_by(Trade.closed_at)
        ).scalars())

        pnls = [float(t.pnl or 0) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        win_rate = (len(wins) / len(pnls)) if pnls else None
        profit_factor = (
            round(sum(wins) / abs(sum(losses)), 4) if losses and wins else None
        )

        snaps = list(self._session.execute(
            select(AccountSnapshot).where(
                AccountSnapshot.account_id == account_id,
                AccountSnapshot.trading_mode == trading_mode,
                AccountSnapshot.snapshot_at >= since,
            ).order_by(AccountSnapshot.snapshot_at)
        ).scalars())
        equity = [float(s.total_balance_usdt) for s in snaps]
        net_return_pct = (
            round((equity[-1] - equity[0]) / equity[0], 6)
            if len(equity) >= 2 and equity[0] > 0 else None
        )
        daily_returns = self._daily_returns(snaps)

        hodl = self._hodl_curve(trading_mode=trading_mode, since=since, account_id=account_id)
        hodl_return_pct = (
            round((hodl[-1][1] - hodl[0][1]) / hodl[0][1], 6)
            if len(hodl) >= 2 and hodl[0][1] > 0 else None
        )

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = sum(1 for t in trades if t.closed_at and self._aware(t.closed_at) >= today_start)
        holdings = [t.holding_seconds for t in trades if t.holding_seconds]
        week_since = now - timedelta(days=7)
        month_since = now - timedelta(days=30)

        return {
            "range_days": range_days,
            "net_return_pct": net_return_pct,
            "hodl_return_pct": hodl_return_pct,
            "vs_hodl_pct": (
                round(net_return_pct - hodl_return_pct, 6)
                if net_return_pct is not None and hodl_return_pct is not None else None
            ),
            "sharpe": _annualized_ratio(daily_returns, downside_only=False),
            "sortino": _annualized_ratio(daily_returns, downside_only=True),
            "max_drawdown_pct": _max_drawdown(equity) if equity else None,
            "win_rate": round(win_rate, 4) if win_rate is not None else None,
            "profit_factor": profit_factor,
            "trades": len(trades),
            "net_pnl": round(sum(pnls), 8),
            # 联调缺口#5: 主控台磁贴
            "today_trades": today_trades,
            "avg_holding_seconds": int(sum(holdings) / len(holdings)) if holdings else None,
            "week_pnl": round(sum(
                float(t.pnl or 0) for t in trades
                if t.closed_at and self._aware(t.closed_at) >= week_since
            ), 8),
            "month_pnl": round(sum(
                float(t.pnl or 0) for t in trades
                if t.closed_at and self._aware(t.closed_at) >= month_since
            ), 8),
            "curve": self._merged_curve(snaps, hodl),
        }

    # ── monthly ─────────────────────────────────────────────────────────

    def monthly(self, *, trading_mode: str, months: int = 12, account_id: int = 1) -> list[dict]:
        since = datetime.now(tz=timezone.utc) - timedelta(days=31 * months)
        trades = list(self._session.execute(
            select(Trade).where(
                Trade.account_id == account_id,
                Trade.trading_mode == trading_mode,
                Trade.closed_at >= since,
            )
        ).scalars())
        buckets: dict[str, dict] = {}
        for t in trades:
            key = self._aware(t.closed_at).strftime("%Y-%m")
            b = buckets.setdefault(key, {"month": key, "pnl": 0.0, "trades": 0})
            b["pnl"] = round(b["pnl"] + float(t.pnl or 0), 8)
            b["trades"] += 1
        return sorted(buckets.values(), key=lambda x: x["month"])

    # ── attribution ─────────────────────────────────────────────────────

    def attribution(self, *, trading_mode: str, dim: str, range_days: int = 90, account_id: int = 1) -> list[dict]:
        if dim not in _ATTRIBUTION_DIMS:
            raise ParamsException(f"dim 必须是 {sorted(_ATTRIBUTION_DIMS)} 之一")
        since = datetime.now(tz=timezone.utc) - timedelta(days=range_days)
        trades = list(self._session.execute(
            select(Trade).where(
                Trade.account_id == account_id,
                Trade.trading_mode == trading_mode,
                Trade.closed_at >= since,
            )
        ).scalars())
        keyer = {
            "symbol": lambda t: t.symbol,
            "strategy": lambda t: t.strategy_mode or "unknown",
            "trigger": lambda t: t.exit_reason or "unknown",
        }[dim]
        buckets: dict[str, dict] = {}
        for t in trades:
            key = keyer(t)
            b = buckets.setdefault(key, {"key": key, "trades": 0, "net_pnl": 0.0, "wins": 0})
            b["trades"] += 1
            pnl = float(t.pnl or 0)
            b["net_pnl"] = round(b["net_pnl"] + pnl, 8)
            if pnl > 0:
                b["wins"] += 1
        out = []
        for b in buckets.values():
            out.append({
                "key": b["key"], "trades": b["trades"],
                "net_pnl": b["net_pnl"],
                "win_rate": round(b["wins"] / b["trades"], 4) if b["trades"] else None,
            })
        return sorted(out, key=lambda x: x["net_pnl"], reverse=True)

    # ── 内部 ────────────────────────────────────────────────────────────

    @staticmethod
    def _aware(dt: datetime) -> datetime:
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    def _daily_returns(self, snaps: list[AccountSnapshot]) -> list[float]:
        """按天取最后一个快照 → 相邻日收益率。"""
        daily: dict[str, float] = {}
        for s in snaps:
            daily[self._aware(s.snapshot_at).strftime("%Y-%m-%d")] = float(s.total_balance_usdt)
        values = [daily[k] for k in sorted(daily)]
        return [
            (values[i] - values[i - 1]) / values[i - 1]
            for i in range(1, len(values)) if values[i - 1] > 0
        ]

    def _hodl_curve(self, *, trading_mode: str, since: datetime, account_id: int) -> list[tuple[str, float]]:
        rows = list(self._session.execute(
            select(Candle).where(
                Candle.account_id == account_id,
                Candle.trading_mode == trading_mode,
                Candle.symbol == _HODL_SYMBOL,
                Candle.open_time >= since,
            ).order_by(Candle.open_time)
        ).scalars())
        return [(self._aware(c.open_time).isoformat(), float(c.close)) for c in rows]

    def _merged_curve(self, snaps: list[AccountSnapshot], hodl: list[tuple[str, float]]) -> list[dict]:
        """策略权益曲线 + HODL 归一化到同起点; 下采样 ≤200 点。"""
        points = [
            {"ts": self._aware(s.snapshot_at).isoformat(), "equity": float(s.total_balance_usdt)}
            for s in snaps
        ]
        if points and hodl and hodl[0][1] > 0:
            base_equity = points[0]["equity"]
            scale = base_equity / hodl[0][1]
            hodl_map = {ts: price * scale for ts, price in hodl}
            hodl_keys = sorted(hodl_map)
            for p in points:
                # 取不晚于该时刻的最近 HODL 点
                candidates = [k for k in hodl_keys if k <= p["ts"]]
                p["hodl"] = round(hodl_map[candidates[-1]], 8) if candidates else None
        step = max(1, len(points) // _CURVE_MAX_POINTS)
        return points[::step]
