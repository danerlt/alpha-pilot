"""FastAPI 共享依赖 — 认证 + 角色守卫 + 交易所 adapter 装配。

从原 src/app/router.py 抽出, 让所有领域 router 复用 get_current_user /
require_admin / get_adapter, 不再各自重复实现。
"""
from __future__ import annotations

from fastapi import Depends, Header, Request
from src.common.exception.errors import ServiceException
from src.common.response.response_code import ErrorCode
from sqlalchemy.orm import Session

from src.core.exchange.binance_adapter import BinanceAdapter
from src.services.auth import (
    decode_access_token,
    ensure_user_is_active,
)
from src.configs.app_configs import get_app_config as get_base_settings, get_settings
from src.db.session import get_db
from src.common.enums import TradingMode


def extract_bearer_token(authorization: str | None) -> str:
    """从 'Bearer <jwt>' 头里抽 token; 缺失 / 非 Bearer 抛 401。

    被 get_current_user 内部调用; 也作为 public util 给其他地方
    (e.g. WebSocket 鉴权) 复用.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise ServiceException("Missing bearer token", error_code=ErrorCode.AUTH_ERROR)
    return authorization.replace("Bearer ", "", 1)


# 兼容老调用 (router.py facade re-export 还指着这个名字)。新代码用 extract_bearer_token.
_extract_bearer_token = extract_bearer_token


def client_meta(request: Request) -> tuple[str | None, str | None]:
    """取审计用的客户端 (ip, user_agent); nginx 反代时真实 IP 在 X-Forwarded-For 第一段。"""
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() \
        or (request.client.host if request.client else None)
    return ip, request.headers.get("user-agent")


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """从 Authorization header 解析 JWT, 返回 User; 异常 → 401/403。

    所有 token 解码 / sub 转 int 的失败统一翻成 401, 避免泄漏成 500
    (前端 401 自动登出依赖此处必须抛 401, 否则会一直卡 loading).
    """
    from src.models.user import User

    token = extract_bearer_token(authorization)
    secret_key = get_base_settings().APP_AUTH_SECRET_KEY
    try:
        payload = decode_access_token(token, secret_key)
    except ValueError as exc:
        # JWT 过期 / 签名错 / payload 解析失败都进这里
        raise ServiceException(f"Invalid token: {exc}", error_code=ErrorCode.AUTH_ERROR) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise ServiceException("Invalid token subject", error_code=ErrorCode.AUTH_ERROR)

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as exc:
        raise ServiceException("Invalid token subject (non-int)", error_code=ErrorCode.AUTH_ERROR) from exc

    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise ServiceException("User not found", error_code=ErrorCode.AUTH_ERROR)
    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise ServiceException(str(exc), error_code=ErrorCode.FORBIDDEN) from exc
    return user


def require_admin(current_user=Depends(get_current_user)):
    try:
        from src.services.auth import ensure_user_is_admin
        ensure_user_is_admin(current_user.role)
    except PermissionError as exc:
        raise ServiceException(str(exc), error_code=ErrorCode.FORBIDDEN) from exc
    return current_user


def get_adapter() -> BinanceAdapter:
    """构造 BinanceAdapter — Commands router / scheduler_jobs / 测试 mock 都从这取.

    把 settings.TRADING_MODE 解出 testnet/mainnet 字符串, 不论是 enum 还是字符串.
    单源装配让"换 adapter"(例如 V0.2 多交易所) 只改这一处.
    """
    settings = get_settings()
    mode = (
        settings.TRADING_MODE.value
        if isinstance(settings.TRADING_MODE, TradingMode)
        else settings.TRADING_MODE
    )
    return BinanceAdapter(
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_API_SECRET,
        trading_mode=mode,
    )
