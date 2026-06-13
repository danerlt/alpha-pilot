"""Admin endpoints — /api/admin/symbols /users /audit-logs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.exception.errors import DBException, ParamsException, ServiceException
from src.common.response.response_code import ErrorCode
from src.controllers.dependencies import client_meta, require_admin
from src.db.session import get_db
from src.models.audit_log import AuditLog
from src.models.symbol_config import SymbolConfig
from src.models.user import User
from src.schemas.symbol_config import SymbolConfigCreate, SymbolConfigUpdate
from src.schemas.user import UserCreate, UserUpdate
from src.services.auth import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── Symbols ──────────────────────────────────────────────────────────────


@router.get("/symbols")
@api_response()
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
@api_response()
def create_symbol_config(
    payload: SymbolConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    symbol = payload.symbol.upper().strip()
    if db.query(SymbolConfig).filter(SymbolConfig.symbol == symbol).first():
        raise ServiceException("Symbol already exists", error_code=ErrorCode.CONFLICT)

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
    ip, user_agent = client_meta(request)
    db.add(AuditLog(
        user_id=current_admin.id,
        action="create", resource_type="symbol_config",
        resource_id=str(item.id),
        after_json={"symbol": item.symbol, "enabled": item.enabled, "timeframe": item.timeframe},
        ip=ip, user_agent=user_agent,
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
@api_response()
def update_symbol_config(
    symbol_id: int, payload: SymbolConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    item = db.query(SymbolConfig).filter(SymbolConfig.id == symbol_id).first()
    if not item:
        raise DBException(error_code=ErrorCode.NOT_FOUND, message="Symbol config not found")

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
    ip, user_agent = client_meta(request)
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
        ip=ip, user_agent=user_agent,
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
@api_response()
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


@router.post("/users")
@api_response()
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """admin 创建账号 — 公开注册按安全审计 C5 禁用, 这是唯一的运行时建号入口。"""
    username = payload.username.strip()
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise ServiceException("Email already exists", error_code=ErrorCode.CONFLICT)
    if db.query(User).filter(User.username == username).first():
        raise ServiceException("Username already exists", error_code=ErrorCode.CONFLICT)

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role.value,
        status=payload.status.value,
    )
    db.add(user)
    db.flush()
    ip, user_agent = client_meta(request)
    db.add(AuditLog(
        user_id=current_admin.id,
        action="create", resource_type="user",
        resource_id=str(user.id),
        after_json={"username": user.username, "email": user.email, "role": user.role, "status": user.status},
        ip=ip, user_agent=user_agent,
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


@router.patch("/users/{user_id}")
@api_response()
def update_user(
    user_id: int, payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise DBException(error_code=ErrorCode.NOT_FOUND, message="User not found")

    before = {"role": user.role, "status": user.status}
    changed = False
    if payload.role is not None and user.role != payload.role.value:
        user.role = payload.role.value
        changed = True
    if payload.status is not None and user.status != payload.status.value:
        user.status = payload.status.value
        changed = True

    if payload.role is None and payload.status is None:
        raise ParamsException("No user fields provided")

    if changed:
        ip, user_agent = client_meta(request)
        db.add(AuditLog(
            user_id=current_admin.id,
            action="update", resource_type="user",
            resource_id=str(user.id),
            before_json=before,
            after_json={"role": user.role, "status": user.status},
            ip=ip, user_agent=user_agent,
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
@api_response()
def list_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    safe_limit = min(max(limit, 1), 200)
    items = db.query(AuditLog).order_by(
        AuditLog.created_at.desc(), AuditLog.id.desc()
    ).limit(safe_limit).all()
    # 操作人用户名映射 (今晚计划 actor 字段; user_id 可能指向已删用户, 留 None)
    actor_ids = {item.user_id for item in items if item.user_id is not None}
    actor_map: dict[int, str] = {}
    if actor_ids:
        for uid, username in db.query(User.id, User.username).filter(User.id.in_(actor_ids)).all():
            actor_map[uid] = username
    return [
        {
            "id": item.id, "user_id": item.user_id,
            "actor": actor_map.get(item.user_id),
            "action": item.action, "resource_type": item.resource_type,
            "resource_id": item.resource_id,
            "before_json": item.before_json, "after_json": item.after_json,
            "ip": item.ip, "user_agent": item.user_agent,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        for item in items
    ]
