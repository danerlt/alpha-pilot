"""system 域响应模型 (webapp 架构 B1/B3)。"""
from __future__ import annotations

from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    two_fa_enabled: bool = False


class LoginOut(BaseModel):
    """二段式 (handoff 3.7): 启用 2FA 的用户第一段只回 requires_2fa+票据。"""

    access_token: str | None = None
    token_type: str | None = None
    user: UserRead | None = None
    requires_2fa: bool = False
    two_fa_token: str | None = None


class LogoutOut(BaseModel):
    ok: bool


class PermissionItemRead(BaseModel):
    key: str
    label: str
    owner: bool
    admin: bool
    trader: bool
    viewer: bool


class PermissionGroupRead(BaseModel):
    group: str
    items: list[PermissionItemRead]


class RolesOut(BaseModel):
    roles: list[str]
    matrix: list[PermissionGroupRead]
    role_aliases: dict[str, str]
    current_role: str


class AgentHistoryItemRead(BaseModel):
    invocation_id: int
    message: str | None = None
    answer: str | None = None
    tools: list[str] = []
    pending_action_id: int | None = None
    occurred_at: str


class AgentActionConfirmOut(BaseModel):
    action_id: int
    status: str
    key: str
    value: object = None


class CatchupEventRead(BaseModel):
    event_id: str
    event_type: str
    envelope: dict


class CatchupOut(BaseModel):
    events: list[CatchupEventRead]
    count: int
    limit: int


class TwoFaSetupOut(BaseModel):
    """secret 仅在 setup 响应出现一次 (扫码需要); verify 后不再可取。"""

    secret: str
    otpauth_uri: str


class TwoFaStatusOut(BaseModel):
    two_fa_enabled: bool
