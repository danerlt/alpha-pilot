"""FastAPI 路由 — 健康检查、数据查询、手动操作。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.shared.config import get_settings
from src.shared.db import get_db
from src.shared.enums import PositionStatus

router = APIRouter()


# ─── Health ───────────────────────────────────────────────────────────────────

@router.get("/")
async def root():
    return RedirectResponse(url="/health")


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "trading_mode": settings.TRADING_MODE.value,
        "version": "0.1.0",
    }


# ─── Positions ────────────────────────────────────────────────────────────────

@router.get("/api/positions")
def list_positions(db: Session = Depends(get_db)):
    """列出所有开仓持仓。"""
    from src.shared.models.position import Position
    settings = get_settings()
    rows = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .order_by(Position.opened_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "symbol": p.symbol,
            "quantity": float(p.quantity),
            "entry_price": float(p.entry_price),
            "current_price": float(p.current_price or 0),
            "stop_loss": float(p.stop_loss),
            "take_profit": float(p.take_profit) if p.take_profit else None,
            "unrealized_pnl": float(p.unrealized_pnl or 0),
            "unrealized_pnl_pct": float(p.unrealized_pnl_pct or 0),
            "opened_at": p.opened_at.isoformat(),
        }
        for p in rows
    ]


@router.post("/api/positions/{position_id}/close")
def manual_close_position(position_id: int, db: Session = Depends(get_db)):
    """手动平仓（绕过 AI 风控，直接执行）。"""
    from src.services.order_execution.executor import close_long
    from src.shared.enums import TradeExitReason
    from src.shared.models.position import Position
    settings = get_settings()
    pos = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.id == position_id,
            Position.status == PositionStatus.OPEN.value,
        )
        .first()
    )
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found or already closed")
    order = close_long(db, pos, TradeExitReason.MANUAL_CLOSE)
    if order is None:
        raise HTTPException(status_code=500, detail="Failed to close position")
    return {"message": "Position closed", "order_id": order.id}


@router.post("/api/positions/close-all")
def close_all_positions(db: Session = Depends(get_db)):
    """一键全部平仓（绕过所有风控）。"""
    from src.services.order_execution.executor import close_long
    from src.shared.enums import TradeExitReason
    from src.shared.models.position import Position
    settings = get_settings()
    open_positions = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .all()
    )
    closed = []
    for pos in open_positions:
        order = close_long(db, pos, TradeExitReason.MANUAL_CLOSE)
        if order:
            closed.append(pos.id)
    return {"closed_positions": closed, "count": len(closed)}


# ─── Trades ───────────────────────────────────────────────────────────────────

@router.get("/api/trades")
def list_trades(limit: int = 50, db: Session = Depends(get_db)):
    """返回最近 N 条已完成交易记录。"""
    from src.shared.models.trade import Trade
    settings = get_settings()
    rows = (
        db.query(Trade)
        .filter(Trade.trading_mode == settings.TRADING_MODE.value)
        .order_by(Trade.closed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "quantity": float(t.quantity),
            "entry_price": float(t.entry_price),
            "exit_price": float(t.exit_price),
            "pnl": float(t.pnl),
            "pnl_pct": float(t.pnl_pct),
            "exit_reason": t.exit_reason,
            "strategy_mode": t.strategy_mode,
            "regime": t.regime,
            "opened_at": t.opened_at.isoformat(),
            "closed_at": t.closed_at.isoformat(),
            "holding_seconds": t.holding_seconds,
        }
        for t in rows
    ]


# ─── Decisions ────────────────────────────────────────────────────────────────

@router.get("/api/decisions")
def list_decisions(limit: int = 20, db: Session = Depends(get_db)):
    """返回最近 N 条 AI 决策记录。"""
    from src.shared.models.decision import AIDecision
    settings = get_settings()
    rows = (
        db.query(AIDecision)
        .filter(AIDecision.trading_mode == settings.TRADING_MODE.value)
        .order_by(AIDecision.decided_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": d.id,
            "symbol": d.symbol,
            "timeframe": d.timeframe,
            "action": d.action,
            "confidence": float(d.confidence) if d.confidence else None,
            "strategy_mode": d.strategy_mode,
            "reasoning": d.reasoning,
            "risk_note": d.risk_note,
            "is_fallback": d.is_fallback,
            "decided_at": d.decided_at.isoformat(),
        }
        for d in rows
    ]


# ─── Risk Events ──────────────────────────────────────────────────────────────

@router.get("/api/risk-events")
def list_risk_events(limit: int = 50, db: Session = Depends(get_db)):
    from src.shared.models.risk_event import RiskEvent
    settings = get_settings()
    rows = (
        db.query(RiskEvent)
        .filter(RiskEvent.trading_mode == settings.TRADING_MODE.value)
        .order_by(RiskEvent.triggered_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "symbol": r.symbol,
            "description": r.description,
            "resolved": r.resolved,
            "triggered_at": r.triggered_at.isoformat(),
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
        for r in rows
    ]


@router.post("/api/risk-events/{event_id}/resolve")
def resolve_risk_event(event_id: int, db: Session = Depends(get_db)):
    """手动解除熔断事件。"""
    from datetime import datetime, timezone
    from src.shared.models.risk_event import RiskEvent
    settings = get_settings()
    event = (
        db.query(RiskEvent)
        .filter(
            RiskEvent.trading_mode == settings.TRADING_MODE.value,
            RiskEvent.id == event_id,
        )
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Risk event not found")
    event.resolved = True
    event.resolved_at = datetime.now(tz=timezone.utc)
    db.commit()
    return {"message": "Risk event resolved", "id": event_id}


# ─── Daily Reports ────────────────────────────────────────────────────────────

@router.get("/api/reports")
def list_reports(limit: int = 30, db: Session = Depends(get_db)):
    from src.shared.models.report import DailyReport
    settings = get_settings()
    rows = (
        db.query(DailyReport)
        .filter(DailyReport.trading_mode == settings.TRADING_MODE.value)
        .order_by(DailyReport.report_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "report_date": r.report_date.isoformat(),
            "total_trades": r.total_trades,
            "winning_trades": r.winning_trades,
            "losing_trades": r.losing_trades,
            "win_rate": float(r.win_rate) if r.win_rate else None,
            "total_pnl": float(r.total_pnl),
            "total_pnl_pct": float(r.total_pnl_pct),
            "max_drawdown": float(r.max_drawdown) if r.max_drawdown else None,
            "risk_events_count": r.risk_events_count,
        }
        for r in rows
    ]


@router.post("/api/reports/generate")
def generate_report(db: Session = Depends(get_db)):
    """手动触发今日日报生成。"""
    from src.services.reporting.reporter import generate_daily_report
    report = generate_daily_report(db)
    return {"message": "Report generated", "report_date": report.report_date.isoformat()}


# ─── Account ──────────────────────────────────────────────────────────────────

@router.get("/api/account")
def get_account(db: Session = Depends(get_db)):
    """返回最新账户快照。"""
    from src.shared.models.account import AccountSnapshot
    settings = get_settings()
    snap = (
        db.query(AccountSnapshot)
        .filter(AccountSnapshot.trading_mode == settings.TRADING_MODE.value)
        .order_by(AccountSnapshot.snapshot_at.desc())
        .first()
    )
    if not snap:
        return {"message": "No account snapshot available"}
    return {
        "total_balance_usdt": float(snap.total_balance_usdt),
        "available_balance_usdt": float(snap.available_balance_usdt),
        "unrealized_pnl": float(snap.unrealized_pnl),
        "daily_pnl": float(snap.daily_pnl),
        "daily_pnl_pct": float(snap.daily_pnl_pct),
        "snapshot_at": snap.snapshot_at.isoformat(),
    }
