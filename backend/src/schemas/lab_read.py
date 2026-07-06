"""lab 域响应模型 (handoff 3.5)。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LabCandidateRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    source: str
    stage: str
    params: dict[str, Any]
    shadow_progress: float
    shadow_days_target: int
    shadow_started_at: str | None = None
    promote_eligible: bool
    promote_blocked_reason: str | None = None
    metrics: dict[str, Any]
    rollback_reason: str | None = None
    created_at: str | None = None


class LabHistoryItemRead(BaseModel):
    action: str
    candidate_id: int | None = None
    candidate_name: str | None = None
    stage: str | None = None
    reason: str | None = None
    operator: str
    at: str | None = None
