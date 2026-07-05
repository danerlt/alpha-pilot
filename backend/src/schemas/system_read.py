"""system 域响应模型 (webapp 架构 B1/B3)。"""
from __future__ import annotations

from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str
    user: UserRead


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
