"""通知 channel 抽象 + 内置实现 (PRD P1 通知系统)。

NotificationChannel: send(message) 推送一条通知; 失败抛异常由上层 NotificationService 容错。
- LogChannel:      兜底, 始终可用, 写 logger (即使没配 Telegram/Email 也留痕)。
- TelegramChannel: 标准库 urllib POST Telegram Bot API (零新依赖)。
- EmailChannel:    标准库 smtplib 发邮件 (零新依赖)。
"""
from __future__ import annotations

import logging
import smtplib
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from typing import Protocol

from src.services.notification.formatter import NotificationMessage

logger = logging.getLogger("notification")


class NotificationChannel(Protocol):
    name: str

    def send(self, message: NotificationMessage) -> None: ...


class LogChannel:
    """兜底 channel: 始终启用, 把通知写进日志, 保证即使未配外部 channel 也有留痕。"""

    name = "log"

    def send(self, message: NotificationMessage) -> None:
        logger.info(
            "[notify:%s] %s — %s", message.severity, message.title, message.body,
        )


class TelegramChannel:
    """Telegram Bot API channel (urllib, 零新依赖)。"""

    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str, timeout: float = 5.0):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._timeout = timeout

    def send(self, message: NotificationMessage) -> None:
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": self._chat_id,
            "text": f"{message.title}\n{message.body}",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            if resp.status >= 300:
                raise RuntimeError(f"telegram send failed: HTTP {resp.status}")


class EmailChannel:
    """SMTP 邮件 channel (smtplib, 零新依赖)。"""

    name = "email"

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addrs: list[str],
        use_tls: bool = True,
        timeout: float = 10.0,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_addr = from_addr
        self._to_addrs = to_addrs
        self._use_tls = use_tls
        self._timeout = timeout

    def send(self, message: NotificationMessage) -> None:
        mime = MIMEText(message.body, "plain", "utf-8")
        mime["Subject"] = message.title
        mime["From"] = self._from_addr
        mime["To"] = ", ".join(self._to_addrs)
        with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as smtp:
            if self._use_tls:
                smtp.starttls()
            if self._username:
                smtp.login(self._username, self._password)
            smtp.sendmail(self._from_addr, self._to_addrs, mime.as_string())
