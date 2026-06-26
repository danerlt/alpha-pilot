"""NotificationService — severity 过滤 + 去重 + 多 channel 容错推送 (PRD P1)。

dispatch(envelope):
  1. format_notification 映射 (非告警事件 → 跳过)
  2. severity < min_severity → 跳过
  3. 同 event_id 已推过 → 跳过 (at-least-once 消费可能重投)
  4. 推送所有 channel; 单 channel 失败不影响其它; 至少一个成功返 True
"""
from __future__ import annotations

import logging
from collections import OrderedDict

from src.services.events.contracts import EventEnvelope
from src.services.notification.channels import (
    EmailChannel,
    LogChannel,
    NotificationChannel,
    TelegramChannel,
)
from src.services.notification.formatter import format_notification, severity_rank

logger = logging.getLogger("notification")

_DEDUP_MAX = 2048  # 去重缓存上限 (LRU, 防内存无限增长)


class NotificationService:
    def __init__(self, channels: list[NotificationChannel], min_severity: str = "warn"):
        self._channels = channels
        self._min_rank = severity_rank(min_severity)
        self._seen: "OrderedDict[str, None]" = OrderedDict()

    def _already_sent(self, event_id: str) -> bool:
        if event_id in self._seen:
            return True
        self._seen[event_id] = None
        if len(self._seen) > _DEDUP_MAX:
            self._seen.popitem(last=False)
        return False

    def dispatch(self, envelope: EventEnvelope) -> bool:
        """返回是否实际推送了 (至少一个 channel 成功)。"""
        message = format_notification(envelope)
        if message is None:
            return False
        if severity_rank(message.severity) < self._min_rank:
            return False
        if self._already_sent(message.event_id):
            return False

        any_ok = False
        for channel in self._channels:
            try:
                channel.send(message)
                any_ok = True
            except Exception:
                logger.exception("notification channel %s send failed", getattr(channel, "name", "?"))
        return any_ok


def build_channels_from_config(cfg) -> list[NotificationChannel]:
    """按配置装配 channel: LogChannel 始终启用; Telegram/Email 按字段是否填写自动加入。"""
    channels: list[NotificationChannel] = [LogChannel()]
    if cfg.NOTIFY_TELEGRAM_BOT_TOKEN and cfg.NOTIFY_TELEGRAM_CHAT_ID:
        channels.append(TelegramChannel(
            bot_token=cfg.NOTIFY_TELEGRAM_BOT_TOKEN, chat_id=cfg.NOTIFY_TELEGRAM_CHAT_ID,
        ))
    if cfg.NOTIFY_EMAIL_SMTP_HOST and cfg.NOTIFY_EMAIL_TO:
        channels.append(EmailChannel(
            host=cfg.NOTIFY_EMAIL_SMTP_HOST, port=cfg.NOTIFY_EMAIL_SMTP_PORT,
            username=cfg.NOTIFY_EMAIL_USERNAME, password=cfg.NOTIFY_EMAIL_PASSWORD,
            from_addr=cfg.NOTIFY_EMAIL_FROM or cfg.NOTIFY_EMAIL_USERNAME,
            to_addrs=list(cfg.NOTIFY_EMAIL_TO), use_tls=cfg.NOTIFY_EMAIL_USE_TLS,
        ))
    return channels


def build_notification_service(cfg) -> NotificationService:
    """从 AppConfig 构建 NotificationService。"""
    return NotificationService(
        channels=build_channels_from_config(cfg),
        min_severity=cfg.NOTIFY_MIN_SEVERITY,
    )
