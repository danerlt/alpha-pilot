"""User 域 Schema — /api/admin/users 入参。"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from src.common.enums import UserRole, UserStatus


class UserCreate(BaseModel):
    """POST /api/admin/users 入参 (admin 创建账号; 公开注册按安全审计 C5 禁用)."""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE


class UserUpdate(BaseModel):
    """PATCH /api/admin/users/{id} 入参 (admin 改 role/status)."""
    role: UserRole | None = None
    status: UserStatus | None = None
