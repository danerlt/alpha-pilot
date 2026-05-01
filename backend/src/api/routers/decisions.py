"""Decisions — /api/decisions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.shared.config import get_settings
from src.shared.db import get_db
from src.shared.models.decision import AIDecision

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("")
def list_decisions(
    # post-Plan5 安全审计 M3: limit 加上限防 DoS / OOM
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回最近 N 条 AI 决策记录 (要求登录)。"""
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
            "id": d.id, "symbol": d.symbol, "timeframe": d.timeframe,
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
