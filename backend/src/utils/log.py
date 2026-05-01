"""日志初始化与工具。

约定：
- 所有模块用 ``get_logger(__name__)`` 获取 logger
- formatter 自动包含 request_id 字段（HTTP 请求级追踪 ID）
- ContextFilter 在 LogRecord 缺失 request_id 时自动填 "-"，避免 formatter 报 KeyError
"""
from __future__ import annotations

import logging
import os
from typing import Optional


class ContextFilter(logging.Filter):
    """为每条 LogRecord 自动注入 request_id 字段。

    HTTP 链路通过 asgi-correlation-id 中间件在 ContextVar 内提供 request_id；
    本 filter 调用 :func:`src.utils.request_id.get_request_id` 读取。
    在 scheduler 进程或非请求上下文中读不到时填 "-"。
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        if not hasattr(record, "request_id"):
            try:
                from src.utils.request_id import get_request_id  # 延迟 import 避免循环

                record.request_id = get_request_id() or "-"
            except Exception:
                record.request_id = "-"
        return True


LOG_FORMAT = (
    "%(asctime)s %(levelname)-8s [%(name)s] "
    "request_id=%(request_id)s "
    "%(filename)s:%(lineno)d %(funcName)s | %(message)s"
)


def init_logger(name: str = "app", file_name: Optional[str] = None) -> None:
    """初始化全局 logging。api 进程入口、scheduler 进程入口都应调用一次。

    幂等：仅在 root logger 还没 handler 时才 basicConfig，避免覆盖 pytest caplog
    等已附着的 handler；如需强制重设，调用方先 ``logging.getLogger().handlers.clear()``。
    """
    root = logging.getLogger()
    # 已经有非 caplog 的非 NullHandler handler，则视为已初始化
    has_real_handler = any(
        not isinstance(h, logging.NullHandler) and h.__class__.__module__ != "_pytest.logging"
        for h in root.handlers
    )
    if has_real_handler:
        return

    fmt = logging.Formatter(LOG_FORMAT)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if file_name:
        os.makedirs("logs", exist_ok=True)
        handlers.append(logging.FileHandler(f"logs/{file_name}", encoding="utf-8"))

    for h in handlers:
        h.setFormatter(fmt)
        h.addFilter(ContextFilter())

    logging.basicConfig(level=logging.INFO, handlers=handlers)


def get_logger(name: str) -> logging.Logger:
    """获取 logger；调用方一般用 ``get_logger(__name__)``。"""
    return logging.getLogger(name)
