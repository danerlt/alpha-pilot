"""HTTP 请求级 request_id 读取工具。

注意：这里的 request_id 是 HTTP 请求追踪 ID（X-Request-ID 头），
与业务幂等键 trace_id（如 ``Order.trace_id = SHA256(...)``）是完全不同的概念，
不要混淆。
"""
from __future__ import annotations

from asgi_correlation_id import correlation_id


def get_request_id() -> str | None:
    """读取当前请求的 request_id。

    HTTP 链路：CorrelationIdMiddleware 已在 ContextVar 中注入；
    scheduler 链路 / 非请求上下文：返回 None。
    """
    return correlation_id.get()


def current_request_id() -> str:
    """便捷别名：拿不到时返 "-"，便于直接拼到日志/响应里。"""
    return get_request_id() or "-"
