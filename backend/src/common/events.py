"""业务事件公共定义。

Stage 3 第 1 波：保留原有事件契约（`src/services/events/contracts.py`），
本文件 re-export 关键事件类，提供 ``from src.common.events import ...`` 的统一入口。
未来如有公共 BaseEvent 抽象，可叠加在此处。
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# Re-export 既有事件契约（保留实质代码在 services/events/contracts.py，避免破坏）
from src.services.events.contracts import (  # noqa: F401
    EVENT_TYPE_REGISTRY,
    EventEnvelope,
)
from src.utils.time import TimeUtils


class BaseEvent(BaseModel):
    """所有业务事件的基类（spec §4.4 通用 schema）。

    注：现有 ``src/services/events/contracts.py`` 中的事件类未直接继承本类，
    阶段 3 后续可逐步迁移。
    """

    user_id: int | None = Field(default=None, description="ws 路由用")
    request_id: str | None = Field(default=None, description="HTTP 链路 ID（如有）")
    occurred_at: datetime = Field(default_factory=TimeUtils.now)
