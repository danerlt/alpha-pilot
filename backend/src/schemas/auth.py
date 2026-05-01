"""Auth 域 Schema — /api/auth/register /login 入参。"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserRegisterCreate(BaseModel):
    """POST /api/auth/register 入参 (V0.1 已禁用公开注册, 仍保留 schema)."""
    username: str
    email: EmailStr
    password: str


class AuthLoginCreate(BaseModel):
    """POST /api/auth/login 入参."""
    email: EmailStr
    password: str
