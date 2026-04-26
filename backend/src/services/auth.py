from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.shared.enums import UserRole, UserStatus

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"
# JWT TTL — post-Plan5 安全审计 H7: 12h → 60min.
# Mainnet 上线后 token 一旦泄露窗口期降到 1h, 配合 H7 完整方案 (jti 撤销表
# + logout 端点) 后可手动撤销.
# V0.1.x 引入 refresh token 流程后, access token 应进一步降到 ~15min.
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(*, subject: str, role: str, secret_key: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def ensure_user_is_active(status: str) -> None:
    if status != UserStatus.ACTIVE.value:
        raise ValueError("User is disabled")


def ensure_user_is_admin(role: str) -> None:
    if role != UserRole.ADMIN.value:
        raise PermissionError("Admin privileges required")
