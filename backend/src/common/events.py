"""业务事件基类。具体事件子类在阶段 3 业务层重组时填充。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.utils.time import TimeUtils


class BaseEvent(BaseModel):
    """所有业务事件的基类。"""

    user_id: int | None = Field(default=None, description="ws 路由用")
    request_id: str | None = Field(default=None, description="HTTP 链路 ID（如有）")
    occurred_at: datetime = Field(default_factory=TimeUtils.now)
