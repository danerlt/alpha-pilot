"""日报生成服务 — 汇总当日交易数据，写入 daily_reports。"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from sqlalchemy import cast, Date, func
from sqlalchemy.orm import Session

from src.shared.config import get_settings
from src.shared.models.report import DailyReport
from src.shared.models.risk_event import RiskEvent
from src.shared.models.trade import Trade

logger = logging.getLogger(__name__)


def generate_daily_report(db: Session, report_date: date | None = None) -> DailyReport:
    """生成指定日期（默认今天）的日报并写入 DB。"""
    settings = get_settings()
    target_date = report_date or date.today()

    trades = (
        db.query(Trade)
        .filter(
            Trade.trading_mode == settings.TRADING_MODE.value,
            cast(Trade.closed_at, Date) == target_date,
        )
        .all()
    )

    total = len(trades)
    wins = sum(1 for t in trades if float(t.pnl) > 0)
    losses = sum(1 for t in trades if float(t.pnl) <= 0)
    total_pnl = sum(float(t.pnl) for t in trades)
    win_rate = wins / total if total > 0 else None

    # PnL% 需要账户余额基准（取今日最早快照）
    from src.shared.models.account import AccountSnapshot
    first_snap = (
        db.query(AccountSnapshot)
        .filter(
            AccountSnapshot.trading_mode == settings.TRADING_MODE.value,
            cast(AccountSnapshot.snapshot_at, Date) == target_date,
        )
        .order_by(AccountSnapshot.snapshot_at.asc())
        .first()
    )
    base_balance = float(first_snap.total_balance_usdt) if first_snap else 1.0
    total_pnl_pct = total_pnl / base_balance if base_balance > 0 else 0.0

    max_single_loss = None
    if trades:
        pnls = [float(t.pnl) for t in trades]
        min_pnl = min(pnls)
        max_single_loss = min_pnl if min_pnl < 0 else None

    # Max drawdown: 累计 PnL 的最大回撤
    max_drawdown = None
    if trades:
        sorted_trades = sorted(trades, key=lambda t: t.closed_at)
        cumulative = 0.0
        peak = 0.0
        min_dd = 0.0
        for t in sorted_trades:
            cumulative += float(t.pnl)
            if cumulative > peak:
                peak = cumulative
            dd = cumulative - peak
            if dd < min_dd:
                min_dd = dd
        max_drawdown = min_dd if min_dd < 0 else None

    # 风控事件数
    risk_count = (
        db.query(func.count(RiskEvent.id))
        .filter(
            RiskEvent.trading_mode == settings.TRADING_MODE.value,
            cast(RiskEvent.triggered_at, Date) == target_date,
        )
        .scalar()
        or 0
    )

    # 构造摘要
    summary = {
        "date": target_date.isoformat(),
        "symbols_traded": list({t.symbol for t in trades}),
        "exit_reasons": {},
    }
    for t in trades:
        r = t.exit_reason
        summary["exit_reasons"][r] = summary["exit_reasons"].get(r, 0) + 1

    # Upsert daily report
    existing = (
        db.query(DailyReport)
        .filter(
            DailyReport.trading_mode == settings.TRADING_MODE.value,
            DailyReport.report_date == target_date,
        )
        .first()
    )
    if existing:
        report = existing
    else:
        report = DailyReport(
            trading_mode=settings.TRADING_MODE.value,
            report_date=target_date,
        )
        db.add(report)

    report.total_trades = total
    report.winning_trades = wins
    report.losing_trades = losses
    report.win_rate = win_rate
    report.total_pnl = total_pnl
    report.total_pnl_pct = total_pnl_pct
    report.max_single_loss = max_single_loss
    report.max_drawdown = max_drawdown
    report.risk_events_count = risk_count
    report.summary = summary

    db.commit()
    db.refresh(report)
    logger.info(
        "Daily report generated for %s: trades=%d win_rate=%.2f pnl=%.4f",
        target_date, total, win_rate or 0, total_pnl,
    )
    return report
