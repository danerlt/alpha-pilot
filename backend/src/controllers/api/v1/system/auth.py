"""Auth endpoints — /api/auth/register /login /me."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.controllers.dependencies import get_current_user
from src.controllers.rate_limit import login_email_limiter, login_ip_limiter
from src.services.auth import (
    create_access_token,
    ensure_user_is_active,
    hash_password,
    verify_password,
)
from src.shared.config import get_base_settings
from src.shared.db import get_db
from src.shared.enums import UserRole, UserStatus
from src.models.user import User

# 用于 timing-equal: user 不存在时也跑一次 verify_password 让响应时延一致,
# 防止 attacker 通过响应时延差推断 email 是否注册.
# 这是一个 hash_password("dummy-password-for-timing-attack-protection") 的预算结果.
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-equal-only")

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
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """密码登录 — 带限流 + timing-equal 防 user enumeration.

    限流 (post-Plan5 安全审计 H4):
      - per-IP 10 次 / 60s
      - per-email 5 次 / 60s
      超阈值返 429 + Retry-After.

    timing-equal: user 不存在时也跑一次 verify_password 让响应时延一致.
    """
    email = payload.email.lower().strip()

    # nginx 经反代时 client.host 是 nginx, 真实 IP 在 X-Forwarded-For 第一段
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() \
        or (request.client.host if request.client else "unknown")
    login_ip_limiter.check(f"login:ip:{ip}")
    login_email_limiter.check(f"login:email:{email}")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # 不存在时跑 dummy verify 让 timing 一致 (~50ms)
        verify_password(payload.password, _DUMMY_PASSWORD_HASH)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
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
