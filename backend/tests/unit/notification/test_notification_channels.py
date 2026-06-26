"""阶段1: channel 抽象 + LogChannel + config 单测。"""
from __future__ import annotations

import logging

from src.configs.app_configs import get_app_config
from src.services.notification.channels import EmailChannel, LogChannel, TelegramChannel
from src.services.notification.formatter import NotificationMessage


def _msg(severity: str = "warn") -> NotificationMessage:
    return NotificationMessage(
        event_id="evt-1", event_type="circuit_breaker.triggered",
        severity=severity, title="🔴 熔断", body="原因: x", trading_mode="testnet",
    )


def test_log_channel_writes_logger():
    """自挂 handler + 自管 logger 状态, 免疫其它测试遗留的全局 logging 配置 (disable/propagate)。"""
    ch = LogChannel()
    assert ch.name == "log"

    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    lg = logging.getLogger("notification")
    handler = _Capture()
    old_level, old_disabled = lg.level, lg.disabled
    lg.addHandler(handler)
    lg.setLevel(logging.INFO)
    lg.disabled = False
    try:
        ch.send(_msg())
    finally:
        lg.removeHandler(handler)
        lg.setLevel(old_level)
        lg.disabled = old_disabled

    assert any("熔断" in r.getMessage() for r in records)


def test_telegram_channel_constructs_without_network():
    ch = TelegramChannel(bot_token="t", chat_id="c")
    assert ch.name == "telegram"


def test_email_channel_constructs_without_network():
    ch = EmailChannel(
        host="smtp.x", port=587, username="u", password="p",
        from_addr="a@x", to_addrs=["b@y"],
    )
    assert ch.name == "email"


def test_notification_config_defaults():
    cfg = get_app_config()
    assert cfg.NOTIFY_ENABLED is True
    assert cfg.NOTIFY_MIN_SEVERITY == "warn"
    assert cfg.NOTIFY_TELEGRAM_BOT_TOKEN == ""
    assert cfg.NOTIFY_EMAIL_TO == []
