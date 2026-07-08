"""手动下单 Schema (handoff P2 §3.2)。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ManualOrderCreate(BaseModel):
    """POST /api/orders 与 /api/orders/precheck 共用入参。"""

    symbol: str = Field(min_length=1, max_length=20)
    side: Literal["BUY", "SELL"]
    type: Literal["MARKET", "LIMIT"] = "MARKET"
    qty: float = Field(gt=0)
    price: float | None = Field(default=None, gt=0)
    sl: float | None = Field(default=None, gt=0)
    tp: float | None = Field(default=None, gt=0)
    reduce_only: bool = False
    client_order_id: str | None = Field(default=None, min_length=1, max_length=40)
    override_checks: list[str] = Field(
        default_factory=list,
        description="人工覆盖的守卫失败项 key 列表 (服务端按 allowlist 交集裁决, 物理项与缺 SL 铁律不可覆盖)",
    )


class SltpUpdate(BaseModel):
    """PATCH /api/positions/{id}/sltp 入参; 至少给一个字段。"""

    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
