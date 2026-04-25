"""FastAPI 共享依赖 — 认证 + 角色守卫。

从原 src/app/router.py 抽出, 让所有领域 router 复用 get_current_user /
require_admin, 不再各自重复实现。
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from src.services.auth import (
    decode_access_token,
    ensure_user_is_active,
)
from src.shared.config import get_base_settings
from src.shared.db import get_db


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.replace("Bearer ", "", 1)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """从 Authorization header 解析 JWT, 返回 User; 异常 → 401/403."""
    from src.shared.models.user import User

    token = _extract_bearer_token(authorization)
    secret_key = get_base_settings().APP_AUTH_SECRET_KEY
    payload = decode_access_token(token, secret_key)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return user


def require_admin(current_user=Depends(get_current_user)):
    try:
        from src.services.auth import ensure_user_is_admin
        ensure_user_is_admin(current_user.role)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return current_user
