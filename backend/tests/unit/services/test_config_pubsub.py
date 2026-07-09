"""ADR-0001 P2：配置变更 Redis 广播 + 订阅重载。"""
import threading
from unittest.mock import MagicMock, patch

from src.services.system.config_pubsub import (
    CONFIG_CHANGED_CHANNEL,
    config_subscriber_loop,
    publish_config_changed,
)


def test_publish_config_changed_publishes_to_channel():
    client = MagicMock()
    publish_config_changed(redis_client=client)
    client.publish.assert_called_once_with(CONFIG_CHANGED_CHANNEL, "changed")


def test_publish_config_changed_swallows_redis_error():
    client = MagicMock()
    client.publish.side_effect = ConnectionError("redis down")
    # 不应抛出（容错，非致命）
    publish_config_changed(redis_client=client)


class _FakePubSub:
    def __init__(self, messages, stop_flag):
        self._messages = list(messages)
        self._stop_flag = stop_flag
        self.subscribed = None

    def subscribe(self, channel):
        self.subscribed = channel

    def get_message(self, timeout=None):
        if self._messages:
            return self._messages.pop(0)
        self._stop_flag.set()  # 消息发完就停循环
        return None


class _FakeClient:
    def __init__(self, pubsub):
        self._pubsub = pubsub

    def pubsub(self):
        return self._pubsub


def test_config_subscriber_loop_refreshes_on_message():
    stop = threading.Event()
    pubsub = _FakePubSub([{"type": "message", "data": "changed"}], stop)
    client = _FakeClient(pubsub)
    with patch("src.services.system.runtime_config.refresh_runtime_settings_safe") as m:
        config_subscriber_loop(stop, redis_client=client)
    assert pubsub.subscribed == CONFIG_CHANGED_CHANNEL
    m.assert_called_once_with(source="pubsub")


def test_config_subscriber_loop_ignores_non_message():
    stop = threading.Event()
    # subscribe 确认帧 type=subscribe, 不应触发 refresh
    pubsub = _FakePubSub([{"type": "subscribe", "data": 1}], stop)
    client = _FakeClient(pubsub)
    with patch("src.services.system.runtime_config.refresh_runtime_settings_safe") as m:
        config_subscriber_loop(stop, redis_client=client)
    m.assert_not_called()
