"""Auth endpoints — /api/auth/register /login /me."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi import Response as HTTPResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.exception.errors import ServiceException
from src.common.response.response_code import ErrorCode
from src.common.response.response_schema import Response
from src.configs.app_configs import get_app_config as get_base_settings
from src.controllers.dependencies import get_current_user
from src.controllers.rate_limit import login_email_limiter, login_ip_limiter
from src.db.session import get_db
from src.models.user import User
from src.schemas.auth import AuthLoginCreate, UserRegisterCreate
from src.schemas.system_read import LoginOut, LogoutOut, TwoFaSetupOut, TwoFaStatusOut, UserRead
from src.services.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_scoped_token,
    decode_access_token,
    ensure_user_is_active,
    hash_password,
    verify_password,
)

# 用于 timing-equal: user 不存在时也跑一次 verify_password 让响应时延一致,
# 防止 attacker 通过响应时延差推断 email 是否注册.
# 这是一个 hash_password("dummy-password-for-timing-attack-protection") 的预算结果.
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-equal-only")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
@api_response()
def register(payload: UserRegisterCreate, db: Session = Depends(get_db)):
    """V0.1 单管理员场景下公开注册被禁用 (post-Plan5 安全审计 C5).

    所有账号必须由 admin 通过 admin_bootstrap (.env DEFAULT_ADMIN_*) 引导,
    或通过 POST /api/admin/users 创建. 公开 register 在生产 = 任何人都能拿
    USER 角色读 /api/positions, /api/trades, /api/account, /api/decisions
    /api/events/catchup 等敏感接口 (虽然只回当前 user 的, 但 V0.1 当前无
    account 隔离, 实际上是全局可读).

    V0.1.x 多账户场景重启用时, 必须改成 invite-token 流程 + 限速 + 邮箱验证.
    """
    raise ServiceException(
        message="Public registration disabled. Contact your admin.",
        error_code=ErrorCode.FORBIDDEN,
    )


AUTH_COOKIE_NAME = "ap_token"


def _cookie_secure() -> bool:
    """uat/prod 走 https → Secure; 本地/dev http 环境不加以免 cookie 被浏览器丢弃。"""
    return get_base_settings().ENVIRONMENT in ("uat", "prod")


@router.post("/login", response_model=Response[LoginOut])
@api_response()
def login(
    payload: AuthLoginCreate,
    request: Request,
    response: HTTPResponse,
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
        raise ServiceException("Invalid credentials", error_code=ErrorCode.AUTH_ERROR)

    if not verify_password(payload.password, user.password_hash):
        raise ServiceException("Invalid credentials", error_code=ErrorCode.AUTH_ERROR)

    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise ServiceException(str(exc), error_code=ErrorCode.FORBIDDEN) from exc

    # handoff 3.7 二段式: 启用 2FA → 只发短期 2fa 票据, 不发正式 token/cookie
    if user.two_fa_enabled:
        return {
            "requires_2fa": True,
            "two_fa_token": create_scoped_token(
                subject=str(user.id), scope="2fa",
                secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
            ),
        }

    user.last_login_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    token = create_access_token(
        subject=str(user.id), role=user.role,
        secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
    )
    # webapp 架构 B3: httpOnly cookie 下发 (token 不落 localStorage 防 XSS),
    # 与 Bearer 头并存, 不破坏既有调用方
    response.set_cookie(
        key=AUTH_COOKIE_NAME, value=token,
        httponly=True, samesite="lax", secure=_cookie_secure(),
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/",
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "status": user.status,
        },
    }


@router.post("/logout", response_model=Response[LogoutOut])
@api_response()
def logout(response: HTTPResponse):
    """清 httpOnly cookie (webapp 架构 B3)。不要求有效 token — 过期也能登出。"""
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=Response[UserRead])
@api_response()
def auth_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status,
        "two_fa_enabled": bool(getattr(current_user, "two_fa_enabled", False)),
    }


# ── 2FA (handoff 3.7, TOTP) ──────────────────────────────────────────────


class TwoFaCodeCreate(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TwoFaLoginCreate(TwoFaCodeCreate):
    two_fa_token: str


def _fernet():
    from src.services.system.runtime_config import build_fernet

    return build_fernet(get_base_settings().APP_CONFIG_MASTER_KEY)


def _verify_totp(user: User, code: str) -> bool:
    import pyotp

    if not user.totp_secret:
        return False
    try:
        secret = _fernet().decrypt(user.totp_secret.encode()).decode()
    except Exception:  # noqa: BLE001
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


@router.post("/2fa/setup", response_model=Response[TwoFaSetupOut])
@api_response()
def two_fa_setup(
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    """生成 TOTP secret + otpauth URI (扫码用); verify 通过前不启用。"""
    import pyotp

    secret = pyotp.random_base32()
    user = db.query(User).filter(User.id == current_user.id).first()
    user.totp_secret = _fernet().encrypt(secret.encode()).decode()
    user.two_fa_enabled = False
    db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name="AlphaPilot",
    )
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/2fa/verify", response_model=Response[TwoFaStatusOut])
@api_response()
def two_fa_verify(
    payload: TwoFaCodeCreate,
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    """验证一次 TOTP code → 启用 2FA。"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not _verify_totp(user, payload.code):
        raise ServiceException("验证码错误", error_code=ErrorCode.AUTH_ERROR)
    user.two_fa_enabled = True
    db.commit()
    return {"two_fa_enabled": True}


@router.post("/2fa/disable", response_model=Response[TwoFaStatusOut])
@api_response()
def two_fa_disable(
    payload: TwoFaCodeCreate,
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    """关闭 2FA (需当前有效 code 防他人关闭)。"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user.two_fa_enabled:
        raise ServiceException("2FA 未启用")
    if not _verify_totp(user, payload.code):
        raise ServiceException("验证码错误", error_code=ErrorCode.AUTH_ERROR)
    user.two_fa_enabled = False
    user.totp_secret = None
    db.commit()
    return {"two_fa_enabled": False}


@router.post("/2fa/login", response_model=Response[LoginOut])
@api_response()
def two_fa_login(
    payload: TwoFaLoginCreate,
    response: HTTPResponse,
    db: Session = Depends(get_db),
):
    """二段式第二段: 2fa 票据 + TOTP code → 正式 token + cookie。"""
    try:
        claims = decode_access_token(
            payload.two_fa_token, get_base_settings().APP_AUTH_SECRET_KEY,
        )
    except ValueError as exc:
        raise ServiceException("Invalid 2FA ticket", error_code=ErrorCode.AUTH_ERROR) from exc
    if claims.get("scope") != "2fa":
        raise ServiceException("Invalid 2FA ticket scope", error_code=ErrorCode.AUTH_ERROR)
    user = db.query(User).filter(User.id == int(claims["sub"])).first()
    if user is None or not user.two_fa_enabled:
        raise ServiceException("Invalid 2FA state", error_code=ErrorCode.AUTH_ERROR)
    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise ServiceException(str(exc), error_code=ErrorCode.FORBIDDEN) from exc
    if not _verify_totp(user, payload.code):
        raise ServiceException("验证码错误", error_code=ErrorCode.AUTH_ERROR)

    user.last_login_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    token = create_access_token(
        subject=str(user.id), role=user.role,
        secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
    )
    response.set_cookie(
        key=AUTH_COOKIE_NAME, value=token,
        httponly=True, samesite="lax", secure=_cookie_secure(),
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/",
    )
    return {
        "access_token": token, "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "status": user.status,
            "two_fa_enabled": True,
        },
    }
