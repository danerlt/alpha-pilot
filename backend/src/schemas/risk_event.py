"""RiskEvent 域 Schema — /api/risk-events 入参。"""
from __future__ import annotations

from pydantic import BaseModel


class RiskEventResolveCreate(BaseModel):
    """POST /api/risk-events/{id}/resolve 入参.

    body 兼容性: reason 可选, 缺省给个标识来源的占位串. 前端最好显式传.
    """
    reason: str = "ui_resolve_via_risk_events"
