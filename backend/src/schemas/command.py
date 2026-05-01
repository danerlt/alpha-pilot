"""Command 域 Schema — /api/commands/* 手动操作 / KillSwitch 入参。

危险操作要求 body.confirmation 字段防误触 (close-all)。
"""
from __future__ import annotations

from pydantic import BaseModel


class CloseAllCreate(BaseModel):
    """POST /api/commands/close-all 入参 — 必须 confirmation == 'CLOSE ALL'."""
    confirmation: str
    reason: str
    account_id: int = 1
    trading_mode: str = "testnet"


class ClosePositionCreate(BaseModel):
    """POST /api/commands/close-position/{id} 入参."""
    reason: str


class ResolveBreakerCreate(BaseModel):
    """POST /api/commands/resolve-breaker/{id} 入参."""
    reason: str


class PauseCreate(BaseModel):
    """POST /api/commands/pause | /resume 入参 (resume 复用同 schema)."""
    reason: str
