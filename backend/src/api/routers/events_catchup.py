"""GET /api/events/catchup?since=<event_id> — 从 event_outbox 表读取断线期间的事件回放。

设计:
  - 客户端 WebSocket 断开后保留 lastEventId
  - 重连时先调本端点拿到 since 之后的所有事件 envelope
  - 然后再 connect WebSocket 实时流; 防漏 + 防重 (前端按 event_id 去重)

为简化, V0.1 上限 limit=500 / since 可为空 (返回最近 500 条 published_at != null)。
spec §3.5 给的 5 分钟 / 500 条 TTL 由前端实现 (这里直接全量返回).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.shared.constants import CATCHUP_LIMIT_HARD_CAP
from src.shared.db import get_db
from src.shared.models.event_store import EventOutbox

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/catchup")
def catchup(
    since: str | None = Query(default=None, description="last event_id; 返回此 id 之后的事件"),
    limit: int = Query(default=200, ge=1, le=CATCHUP_LIMIT_HARD_CAP),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回 [event_id 比 since 大] 的事件 envelope, 按 id 升序."""
    stmt = select(EventOutbox).where(EventOutbox.published_at.is_not(None))
    if since:
        # since 是 UUIDv7, 直接按字符串比较即可 (UUIDv7 时间有序)
        stmt = stmt.where(EventOutbox.event_id > since)
    stmt = stmt.order_by(EventOutbox.id.asc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return {
        "events": [
            {
                "event_id": r.event_id,
                "event_type": r.event_type,
                "envelope": r.payload_json,
            }
            for r in rows
        ],
        "count": len(rows),
        "limit": limit,
    }
