"""NotificationDispatcher — Redis Streams consumer group "notifier" 消费告警 (PRD P1)。

scheduler 进程内 daemon: 订阅 ALERT_EVENT_TYPES 对应的 stream, consumer group "notifier"
(event_bus.py docstring 预留), at-least-once + ack——告警不能因进程重启而丢。

  consume_multi → service.dispatch → ack
"""
from __future__ import annotations

import logging
import threading
from typing import Iterator, Protocol

from src.services.events.contracts import EventEnvelope
from src.services.notification.formatter import ALERT_EVENT_TYPES
from src.services.notification.service import NotificationService

logger = logging.getLogger("notification")

NOTIFIER_GROUP = "notifier"


class _StreamsBusLike(Protocol):
    def ensure_group(self, stream: str, group: str) -> None: ...
    def consume_multi(
        self, streams: list[str], group: str, consumer: str, *, count: int = ..., block_ms: int = ...,
    ) -> Iterator[tuple[str, str, EventEnvelope]]: ...
    def ack(self, stream: str, group: str, message_id: str) -> int: ...


class NotificationDispatcher:
    def __init__(
        self,
        bus: _StreamsBusLike,
        service: NotificationService,
        *,
        streams: list[str] | None = None,
        consumer: str = "notifier-1",
    ):
        self._bus = bus
        self._service = service
        self._streams = streams if streams is not None else sorted(ALERT_EVENT_TYPES)
        self._consumer = consumer

    def setup(self) -> None:
        """对每个告警 stream 幂等创建 notifier consumer group。"""
        for stream in self._streams:
            self._bus.ensure_group(stream, NOTIFIER_GROUP)

    def run_once(self, *, block_ms: int = 2000) -> int:
        """消费一批: dispatch + ack; 返回处理条数。"""
        handled = 0
        for stream, msg_id, envelope in self._bus.consume_multi(
            self._streams, NOTIFIER_GROUP, self._consumer, block_ms=block_ms,
        ):
            try:
                self._service.dispatch(envelope)
            except Exception:
                logger.exception("notification dispatch failed for %s %s", stream, msg_id)
            finally:
                # 即便 dispatch 失败也 ack: 告警是尽力而为, 不阻塞 stream
                # (channel 层已各自容错; 真失败已留日志)
                try:
                    self._bus.ack(stream, NOTIFIER_GROUP, msg_id)
                except Exception:
                    logger.exception("ack failed for %s %s", stream, msg_id)
            handled += 1
        return handled

    def loop(self, stop_flag: threading.Event, *, block_ms: int = 2000) -> None:
        logger.info("NotificationDispatcher loop started (streams=%d)", len(self._streams))
        self.setup()
        while not stop_flag.is_set():
            try:
                self.run_once(block_ms=block_ms)
            except Exception:
                logger.exception("notification loop unhandled error")
                stop_flag.wait(1.0)
        logger.info("NotificationDispatcher loop stopping")
