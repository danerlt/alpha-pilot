"""WebSocket endpoint — 订阅 Redis 多频道, 实时推送给前端。

Critical fix C4:
  - accept 之前先校验 ?token=<jwt>; 失败立即 close(4401).
  - 握手成功后, 如果带 ?since=<event_id>, 从 event_outbox 回放断线期间事件再开始
    实时订阅, 防漏 + 防重 (前端按 event_id 去重)。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy import select

from src.services.auth import decode_access_token, ensure_user_is_active
from src.shared.config import get_base_settings
from src.shared.db import get_session_factory
from src.shared.models.event_store import EventOutbox

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理所有活跃的 WebSocket 连接."""

    def __init__(self) -> None:
        self._active: Set[WebSocket] = set()

    async def add(self, ws: WebSocket) -> None:
        self._active.add(ws)
        logger.info("WS client added, total=%d", len(self._active))

    def remove(self, ws: WebSocket) -> None:
        self._active.discard(ws)
        logger.info("WS client removed, total=%d", len(self._active))

    async def broadcast(self, message: str) -> None:
        dead: Set[WebSocket] = set()
        for ws in self._active.copy():
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._active.discard(ws)

    @property
    def count(self) -> int:
        return len(self._active)


manager = ConnectionManager()


def _verify_token(token: str | None) -> int:
    """解析 ?token= 的 JWT, 返回 user_id; 失败抛 WebSocketException(4401).

    用 4xxx 范围里的 close code (RFC 6455 application-defined) 给前端区分:
      4401 = unauthenticated  (类比 HTTP 401)
      4403 = user disabled    (类比 HTTP 403)
    """
    if not token:
        raise WebSocketException(code=4401, reason="missing token")
    try:
        secret_key = get_base_settings().APP_AUTH_SECRET_KEY
        payload = decode_access_token(token, secret_key)
        sub = payload.get("sub")
        if not sub:
            raise WebSocketException(code=4401, reason="invalid token subject")
        return int(sub)
    except WebSocketException:
        raise
    except Exception as e:  # noqa: BLE001
        raise WebSocketException(code=4401, reason=f"jwt decode failed: {e}") from e


async def _replay_since(ws: WebSocket, since: str | None, limit: int = 200) -> None:
    """握手成功后回放断线期间事件 — 从 event_outbox 表读 published_at != null 且
    event_id > since 的行, 按 id 升序 send_text, 前端按 event_id 去重.

    catchup 上限 200 (HTTP /api/events/catchup 也是 200 默认), 历史更长的事件
    需走 GET /api/events/catchup 显式拉取分页.
    """
    if not since:
        return
    SessionLocal = get_session_factory()
    try:
        with SessionLocal() as db:
            rows = db.execute(
                select(EventOutbox).where(
                    EventOutbox.published_at.is_not(None),
                    EventOutbox.event_id > since,
                ).order_by(EventOutbox.id.asc()).limit(limit)
            ).scalars().all()
            for row in rows:
                envelope_json = json.dumps(row.payload_json)
                try:
                    await ws.send_text(envelope_json)
                except Exception:
                    return  # 客户端在回放期间断了, 不再继续
    except Exception:
        logger.exception("replay_since error (non-fatal)")


async def websocket_endpoint(ws: WebSocket) -> None:
    """FastAPI WebSocket 路由处理函数。

    握手协议:
      ws://host/ws?token=<jwt>&since=<last_event_id>

    流程:
      1. 校验 token; 失败 close(4401)
      2. accept
      3. 若带 since, 回放 event_outbox > since 的事件 (catchup)
      4. 注册到 ConnectionManager 进入实时广播循环
    """
    token = ws.query_params.get("token")
    since = ws.query_params.get("since")

    try:
        _verify_token(token)
    except WebSocketException as e:
        # 必须 accept 之后才能 close, 否则握手层直接 403
        await ws.accept()
        await ws.close(code=e.code, reason=str(e.reason or ""))
        return

    await ws.accept()
    await _replay_since(ws, since)
    await manager.add(ws)
    try:
        while True:
            # 保持连接, 忽略客户端消息 (只做服务端推送)
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(ws)


async def redis_subscriber(redis_url: str) -> None:
    """后台任务: 订阅 Redis 多通道 (events:* + trading_events 兼容) 并广播给 WS 客户端.

    events:<event_type> 是 Plan 5 加的细粒度通道, trading_events 是旧版兼容
    通道, 同一条事件双发 (见 EventShuttle._pubsub 旁路).
    """
    logger.info("Redis subscriber task starting, url=%s", redis_url)
    while True:
        try:
            r: aioredis.Redis = aioredis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe("trading_events")
            await pubsub.psubscribe("events:*")
            logger.info("Subscribed: trading_events + pattern events:*")
            async for message in pubsub.listen():
                if message["type"] in ("message", "pmessage"):
                    await manager.broadcast(message["data"])
        except asyncio.CancelledError:
            logger.info("Redis subscriber task cancelled")
            return
        except Exception as e:
            logger.error("Redis subscriber error: %s — reconnecting in 5s", e)
            await asyncio.sleep(5)
