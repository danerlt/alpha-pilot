"""WebSocket 连接管理器 — 维护活跃连接集合, 提供广播 / 进出登记。

从 src/controllers/websocket.py 抽出, 让 controller 层只剩路由 + 鉴权,
ConnectionManager 作为可独立测试 / 复用的 service 单例。

注意: V0.1 单进程内存方案。多 worker 部署时需要走 Redis Pub/Sub
跨进程广播 (controllers/websocket.py 的 redis_subscriber 已实现该路径)。
"""
from __future__ import annotations

import logging
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSConnectionManager:
    """管理所有活跃的 WebSocket 连接。"""

    def __init__(self) -> None:
        self._active: Set[WebSocket] = set()

    async def add(self, ws: WebSocket) -> None:
        self._active.add(ws)
        logger.info("WS client added, total=%d", len(self._active))

    def remove(self, ws: WebSocket) -> None:
        self._active.discard(ws)
        logger.info("WS client removed, total=%d", len(self._active))

    async def broadcast(self, message: str) -> None:
        """向所有活跃连接发送消息; 出错的连接自动剔除。"""
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


# 进程内单例 — controllers / scheduler subscriber 共享
ws_manager = WSConnectionManager()
