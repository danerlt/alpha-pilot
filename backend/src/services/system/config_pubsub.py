"""配置变更 Redis 广播 + 订阅重载（ADR-0001 P2）。

写配置提交后 publish 一条到 ``alphapilot:config``；各进程（API worker / scheduler）
订到即从 DB 重载 runtime 配置单例 → 毫秒级下发 + 多 worker 强一致。

Pub/Sub 尽力投递：订阅者重启会漏消息，靠 P1 周期兜底刷新自愈（ADR §7）。
"""
from __future__ import annotations

import asyncio
import logging
import threading

logger = logging.getLogger("config_pubsub")

CONFIG_CHANGED_CHANNEL = "alphapilot:config"


def publish_config_changed(redis_client=None) -> None:
    """写配置后广播变更。容错：Redis 不可用只 warning，不影响主流程。"""
    try:
        if redis_client is None:
            from src.utils.redis import get_redis_client

            redis_client = get_redis_client()
        redis_client.publish(CONFIG_CHANGED_CHANNEL, "changed")
    except Exception:  # noqa: BLE001
        logger.warning("publish config change failed (non-fatal)", exc_info=True)


def config_subscriber_loop(stop_flag: threading.Event, redis_client=None) -> None:
    """scheduler 进程常驻线程：订阅 config 频道，收到即从 DB 重载 runtime 配置。

    get_message(timeout) 轮询，保证 stop_flag 能及时响应优雅退出。
    """
    from src.services.system.runtime_config import refresh_runtime_settings_safe

    if redis_client is None:
        from src.utils.redis import get_redis_client

        redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    pubsub.subscribe(CONFIG_CHANGED_CHANNEL)
    logger.info("Config subscriber started, channel=%s", CONFIG_CHANGED_CHANNEL)
    while not stop_flag.is_set():
        try:
            msg = pubsub.get_message(timeout=1.0)
        except Exception:  # noqa: BLE001
            logger.warning("config subscriber get_message failed; retry", exc_info=True)
            continue
        if msg and msg.get("type") == "message":
            refresh_runtime_settings_safe(source="pubsub")


async def config_subscriber_task(redis_url: str) -> None:
    """API 进程 lifespan 后台任务：订阅 config 频道，收到即从 DB 重载（每 worker 各跑一份）。"""
    import redis.asyncio as aioredis

    from src.services.system.runtime_config import refresh_runtime_settings_safe

    loop = asyncio.get_event_loop()
    while True:
        try:
            client = aioredis.from_url(redis_url, decode_responses=True)
            pubsub = client.pubsub()
            await pubsub.subscribe(CONFIG_CHANGED_CHANNEL)
            logger.info("Config subscriber task subscribed, channel=%s", CONFIG_CHANGED_CHANNEL)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await loop.run_in_executor(
                        None, lambda: refresh_runtime_settings_safe(source="pubsub")
                    )
        except asyncio.CancelledError:
            logger.info("Config subscriber task cancelled")
            return
        except Exception as e:  # noqa: BLE001
            logger.error("Config subscriber error: %s — reconnecting in 5s", e)
            await asyncio.sleep(5)
