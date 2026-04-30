"""Redis 客户端工厂。同步/异步并存。

- 同步客户端：用于 scheduler 容器主线程 BRPOP（阻塞操作）+ 业务侧 lpush/get 等同步调用
- 异步客户端：用于 api 容器 lifespan 协程的 Redis Pub/Sub 订阅
- 进程内单例，按需创建
"""
from __future__ import annotations

from typing import Optional

import redis as sync_redis
import redis.asyncio as async_redis

_sync_client: Optional[sync_redis.Redis] = None
_async_client: Optional[async_redis.Redis] = None


def get_redis_client() -> sync_redis.Redis:
    """同步 Redis 客户端单例。"""
    global _sync_client
    if _sync_client is None:
        from src.configs import get_app_config

        cfg = get_app_config()
        _sync_client = sync_redis.from_url(cfg.REDIS_URL, decode_responses=True)
    return _sync_client


def get_async_redis() -> async_redis.Redis:
    """异步 Redis 客户端单例（仅 api 容器 lifespan 使用）。"""
    global _async_client
    if _async_client is None:
        from src.configs import get_app_config

        cfg = get_app_config()
        _async_client = async_redis.from_url(cfg.REDIS_URL, decode_responses=True)
    return _async_client


def reset_redis_clients() -> None:
    """单测使用：重置单例。生产代码不应调用。"""
    global _sync_client, _async_client
    if _sync_client is not None:
        try:
            _sync_client.close()
        except Exception:
            pass
    _sync_client = None
    _async_client = None
