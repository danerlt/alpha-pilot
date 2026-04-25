"""WebSocket endpoint — 订阅 Redis trading_events 频道，实时推送给前端。"""
from __future__ import annotations

import asyncio
import logging
from typing import Set

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理所有活跃的 WebSocket 连接。"""

    def __init__(self) -> None:
        self._active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.add(ws)
        logger.info("WS client connected, total=%d", len(self._active))

    def disconnect(self, ws: WebSocket) -> None:
        self._active.discard(ws)
        logger.info("WS client disconnected, total=%d", len(self._active))

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


async def websocket_endpoint(ws: WebSocket) -> None:
    """FastAPI WebSocket 路由处理函数。"""
    await manager.connect(ws)
    try:
        while True:
            # 保持连接，忽略客户端消息（只做服务端推送）
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws)


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
