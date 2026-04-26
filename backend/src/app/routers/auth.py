"""Auth endpoints — /api/auth/register /login /me."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.app.dependencies import get_current_user
from src.services.auth import (
    create_access_token,
    ensure_user_is_active,
    hash_password,
    verify_password,
)
from src.shared.config import get_base_settings
from src.shared.db import get_db
from src.shared.enums import UserRole, UserStatus
from src.shared.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """V0.1 单管理员场景下公开注册被禁用 (post-Plan5 安全审计 C5).

    所有账号必须由 admin 通过 admin_bootstrap (.env DEFAULT_ADMIN_*) 引导,
    或通过 POST /api/admin/users 创建. 公开 register 在生产 = 任何人都能拿
    USER 角色读 /api/positions, /api/trades, /api/account, /api/decisions
    /api/events/catchup 等敏感接口 (虽然只回当前 user 的, 但 V0.1 当前无
    account 隔离, 实际上是全局可读).

    V0.1.x 多账户场景重启用时, 必须改成 invite-token 流程 + 限速 + 邮箱验证.
    """
    raise HTTPException(
        status_code=403,
        detail="Public registration disabled. Contact your admin.",
    )


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    user.last_login_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    token = create_access_token(
        subject=str(user.id), role=user.role,
        secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "status": user.status,
        },
    }


@router.get("/me")
def auth_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status,
    }
