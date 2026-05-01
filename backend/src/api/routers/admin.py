"""Admin endpoints — /api/admin/symbols /users /audit-logs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.dependencies import require_admin
from src.shared.db import get_db
from src.shared.enums import UserRole, UserStatus
from src.shared.models.audit_log import AuditLog
from src.shared.models.symbol_config import SymbolConfig
from src.shared.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


class SymbolConfigCreate(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str = "USDT"
    enabled: bool = True
    timeframe: str = "15m"
    max_position_size_pct: float | None = None
    priority: int = 100
    sort_order: int = 100
    notes: str | None = None


class SymbolConfigUpdate(BaseModel):
    base_asset: str | None = None
    quote_asset: str | None = None
    enabled: bool | None = None
    timeframe: str | None = None
    max_position_size_pct: float | None = None
    priority: int | None = None
    sort_order: int | None = None
    notes: str | None = None


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    status: UserStatus | None = None


# ─── Symbols ──────────────────────────────────────────────────────────────


@router.get("/symbols")
def list_symbol_configs(db: Session = Depends(get_db), current_admin=Depends(require_admin)):
    items = db.query(SymbolConfig).order_by(
        SymbolConfig.sort_order.asc(), SymbolConfig.symbol.asc()
    ).all()
    return [
        {
            "id": item.id, "symbol": item.symbol,
            "base_asset": item.base_asset, "quote_asset": item.quote_asset,
            "enabled": item.enabled, "timeframe": item.timeframe,
            "max_position_size_pct": item.max_position_size_pct,
            "priority": item.priority, "sort_order": item.sort_order,
            "notes": item.notes,
        }
        for item in items
    ]


@router.post("/symbols")
def create_symbol_config(
    payload: SymbolConfigCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    symbol = payload.symbol.upper().strip()
    if db.query(SymbolConfig).filter(SymbolConfig.symbol == symbol).first():
        raise HTTPException(status_code=409, detail="Symbol already exists")

    item = SymbolConfig(
        symbol=symbol,
        base_asset=payload.base_asset.upper().strip(),
        quote_asset=payload.quote_asset.upper().strip(),
        enabled=payload.enabled,
        timeframe=payload.timeframe,
        max_position_size_pct=payload.max_position_size_pct,
        priority=payload.priority,
        sort_order=payload.sort_order,
        notes=payload.notes,
        created_by=current_admin.id,
        updated_by=current_admin.id,
    )
    db.add(item)
    db.flush()
    db.add(AuditLog(
        user_id=current_admin.id,
        action="create", resource_type="symbol_config",
        resource_id=str(item.id),
        after_json={"symbol": item.symbol, "enabled": item.enabled, "timeframe": item.timeframe},
    ))
    db.commit()
    db.refresh(item)
    return {
        "id": item.id, "symbol": item.symbol,
        "base_asset": item.base_asset, "quote_asset": item.quote_asset,
        "enabled": item.enabled, "timeframe": item.timeframe,
        "max_position_size_pct": item.max_position_size_pct,
        "priority": item.priority, "sort_order": item.sort_order,
        "notes": item.notes,
    }


@router.patch("/symbols/{symbol_id}")
def update_symbol_config(
    symbol_id: int, payload: SymbolConfigUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    item = db.query(SymbolConfig).filter(SymbolConfig.id == symbol_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Symbol config not found")

    before = {
        "enabled": item.enabled, "timeframe": item.timeframe,
        "max_position_size_pct": item.max_position_size_pct,
        "priority": item.priority, "sort_order": item.sort_order,
        "notes": item.notes,
    }

    for field in ["base_asset", "quote_asset", "enabled", "timeframe",
                  "max_position_size_pct", "priority", "sort_order", "notes"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value.upper().strip() if field in {"base_asset", "quote_asset"} else value)
    item.updated_by = current_admin.id
    db.add(AuditLog(
        user_id=current_admin.id,
        action="update", resource_type="symbol_config",
        resource_id=str(item.id),
        before_json=before,
        after_json={
            "enabled": item.enabled, "timeframe": item.timeframe,
            "max_position_size_pct": item.max_position_size_pct,
            "priority": item.priority, "sort_order": item.sort_order,
            "notes": item.notes,
        },
    ))
    db.commit()
    db.refresh(item)
    return {
        "id": item.id, "symbol": item.symbol,
        "base_asset": item.base_asset, "quote_asset": item.quote_asset,
        "enabled": item.enabled, "timeframe": item.timeframe,
        "max_position_size_pct": item.max_position_size_pct,
        "priority": item.priority, "sort_order": item.sort_order,
        "notes": item.notes,
    }


# ─── Users ────────────────────────────────────────────────────────────────


@router.get("/users")
def list_users(db: Session = Depends(get_db), current_admin=Depends(require_admin)):
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        {
            "id": u.id, "username": u.username, "email": u.email,
            "role": u.role, "status": u.status,
            "last_login_at": u.last_login_at,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
        }
        for u in users
    ]


@router.patch("/users/{user_id}")
def update_user(
    user_id: int, payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before = {"role": user.role, "status": user.status}
    changed = False
    if payload.role is not None and user.role != payload.role.value:
        user.role = payload.role.value
        changed = True
    if payload.status is not None and user.status != payload.status.value:
        user.status = payload.status.value
        changed = True

    if payload.role is None and payload.status is None:
        raise HTTPException(status_code=400, detail="No user fields provided")

    if changed:
        db.add(AuditLog(
            user_id=current_admin.id,
            action="update", resource_type="user",
            resource_id=str(user.id),
            before_json=before,
            after_json={"role": user.role, "status": user.status},
        ))
        db.commit()
        db.refresh(user)

    return {
        "id": user.id, "username": user.username, "email": user.email,
        "role": user.role, "status": user.status,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


# ─── Audit logs ───────────────────────────────────────────────────────────


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    safe_limit = min(max(limit, 1), 200)
    items = db.query(AuditLog).order_by(
        AuditLog.created_at.desc(), AuditLog.id.desc()
    ).limit(safe_limit).all()
    return [
        {
            "id": item.id, "user_id": item.user_id,
            "action": item.action, "resource_type": item.resource_type,
            "resource_id": item.resource_id,
            "before_json": item.before_json, "after_json": item.after_json,
            "ip": item.ip, "user_agent": item.user_agent,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        for item in items
    ]
