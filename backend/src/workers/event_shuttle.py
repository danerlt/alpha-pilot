"""EventShuttle — moves unpublished event_outbox rows to Redis Streams.

stream_for_event(event_type) maps "candle.closed" -> "candle.closed" by default;
override to route all trade.* to the same stream, etc.

Failure handling:
  - Each publish error increments failed_attempts and records last_error.
  - After max_failed_attempts (configurable), the envelope is pushed to the
    dead-letter stream (via bus.dead_letter) and the row is marked
    published_at to prevent infinite re-processing.
  - Even if the dead-letter publish itself fails, the row is still marked
    published_at to guarantee progress (last_error 留存死信失败原因);
    数据没丢 — 仍在 event_outbox 表里, 后续可手动重放.

可配 (Plan 5 codereview I10):
  EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS .env 覆盖默认 3.

  阈值含义: 每次失败 failed_attempts += 1, 当 failed_attempts >= 阈值 即死信.
    阈值=3 → 累计 3 次失败时死信 (相当于 1 次首发 + 2 次重试)
    阈值=2 → 累计 2 次失败时死信 (相当于 1 次首发 + 1 次重试)
    阈值=1 → 第 1 次失败即死信 (无重试)
    阈值=0 (或负数, 内部 clamp 到 0) → 同 1, 首次失败即死信
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.events.contracts import EventEnvelope
from src.shared.constants import DEFAULT_EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS
from src.models.event_store import EventOutbox

logger = logging.getLogger(__name__)

# 兼容旧名: 一些测试 import 这个常量名. 实际值已迁到 shared/constants.py.
DEFAULT_MAX_FAILED_ATTEMPTS = DEFAULT_EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS


class _BusLike(Protocol):
    def publish(self, stream: str, envelope: EventEnvelope, **kw) -> str | None: ...
    def dead_letter(self, stream: str, envelope: EventEnvelope, reason: str) -> None: ...


class _PubSubLike(Protocol):
    def publish(self, channel: str, message: str) -> int: ...


class EventShuttle:
    def __init__(
        self,
        engine: Engine,
        bus: _BusLike,
        stream_for_event: Callable[[str], str] = lambda t: t,
        pubsub: _PubSubLike | None = None,
        max_failed_attempts: Optional[int] = None,
    ):
        """`pubsub` 可选: 如果提供, 每条事件除了写 Streams 之外还 publish 到
        `events:{event_type}` 和 `trading_events` (兼容老订阅) Pub/Sub 频道,
        让 WebSocket 等即时订阅者能立即收到 (不需要等 XREAD)。

        max_failed_attempts: 死信阈值. None → 从 settings 读取
        EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS, 缺省 DEFAULT_MAX_FAILED_ATTEMPTS=3.
        显式传值 (含 0) 优先, 方便单测.
        """
        self._engine = engine
        self._bus = bus
        self._stream_for_event = stream_for_event
        self._pubsub = pubsub
        if max_failed_attempts is None:
            try:
                from src.shared.config import get_settings  # 延迟避免循环
                max_failed_attempts = int(get_settings().EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS)
            except Exception:
                max_failed_attempts = DEFAULT_MAX_FAILED_ATTEMPTS
        self._max_failed_attempts = max(0, max_failed_attempts)

    def drain_once(self, batch_size: int = 100) -> int:
        """Publish up to batch_size unpublished rows. Returns count successfully published."""
        published = 0
        with Session(self._engine) as s:
            rows = (
                s.execute(
                    select(EventOutbox)
                    .where(EventOutbox.published_at.is_(None))
                    .order_by(EventOutbox.id.asc())
                    .limit(batch_size)
                )
                .scalars()
                .all()
            )
            for row in rows:
                try:
                    envelope = EventEnvelope.model_validate(row.payload_json)
                    stream = self._stream_for_event(row.event_type)
                    self._bus.publish(stream, envelope)
                    if self._pubsub is not None:
                        try:
                            payload_json = envelope.model_dump_json()
                            # 多频道发布: events:<event_type> 用于精细订阅,
                            # trading_events 兼容旧 WebSocket 订阅。
                            self._pubsub.publish(f"events:{row.event_type}", payload_json)
                            self._pubsub.publish("trading_events", payload_json)
                        except Exception:
                            logger.exception("pubsub publish failed (non-fatal)")
                    row.published_at = datetime.now(timezone.utc)
                    published += 1
                except Exception as e:  # noqa: BLE001 — broad on purpose
                    row.failed_attempts += 1
                    row.last_error = str(e)[:500]
                    logger.exception("shuttle failed for outbox row id=%s", row.id)
                    if row.failed_attempts >= self._max_failed_attempts:
                        try:
                            envelope = EventEnvelope.model_validate(row.payload_json)
                            self._bus.dead_letter(
                                self._stream_for_event(row.event_type),
                                envelope,
                                reason=row.last_error or "unknown",
                            )
                        except Exception as dl_err:
                            # 死信本身也失败 → 仍要标 published_at, 否则会无限重试
                            # dead_letter; row 本身的 last_error / payload_json 仍在 DB,
                            # 后续可手动重放或人工处理.
                            row.last_error = (
                                f"{row.last_error} | dead_letter_failed:{dl_err}"
                            )[:500]
                            logger.exception("dead-letter publish also failed for row id=%s", row.id)
                        # 无论 dead_letter 是否成功, 标 published_at 防卡死
                        row.published_at = datetime.now(timezone.utc)
            s.commit()
        return published

    def run_forever(self, *, poll_interval_seconds: float = 1.0) -> None:
        while True:
            try:
                self.drain_once()
            except Exception:
                logger.exception("shuttle drain loop error")
            time.sleep(poll_interval_seconds)
