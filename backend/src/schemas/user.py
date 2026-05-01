"""User 域 Schema — /api/admin/users PATCH 入参。"""
from __future__ import annotations

from pydantic import BaseModel

from src.common.enums import UserRole, UserStatus


class UserUpdate(BaseModel):
    """PATCH /api/admin/users/{id} 入参 (admin 改 role/status)."""
    role: UserRole | None = None
    status: UserStatus | None = None
