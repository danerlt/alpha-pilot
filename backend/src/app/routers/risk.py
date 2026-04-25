"""Risk events — /api/risk-events /api/risk-events/{id}/resolve."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.shared.config import get_settings
from src.shared.db import get_db

router = APIRouter(prefix="/api/risk-events", tags=["risk"])


@router.get("")
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
            "id": r.id, "event_type": r.event_type, "symbol": r.symbol,
            "description": r.description, "resolved": r.resolved,
            "triggered_at": r.triggered_at.isoformat(),
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
        for r in rows
    ]


@router.post("/{event_id}/resolve")
def resolve_risk_event(event_id: int, db: Session = Depends(get_db)):
    """手动解除熔断事件。"""
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
