"""幂等 trace_id 生成器 — 写订单 / 任务 / 操作时用作业务幂等键。

trace_id = SHA256(decision_id:symbol:action) 截断到 32 位 hex。

为啥截断 32 位:
- 32 hex chars = 128 bit, 与 UUID 等强度, 重复风险可忽略
- DB 列定义 String(64), 留头让未来扩到 64 位无需 schema 变更
- 与 request_id (32 char uuid hex) 长度一致, 日志对齐美观

使用场景:
- ``services/execution/order_executor.py``: 写 Order/Position/Trade 时确保
  同一 decision 不会被重复执行 (重启 / 重试场景)
- 未来 task_dispatcher 也会用类似生成器做任务幂等
"""
from __future__ import annotations

import hashlib


def generate_trace_id(decision_id: int, symbol: str, action: str) -> str:
    """生成订单级幂等 trace_id。

    参数:
        decision_id: 决策行 id (decisions 表主键)
        symbol: 交易对 (e.g. ``BTCUSDT``)
        action: 动作字符串 (e.g. ``OPEN_LONG`` / ``CLOSE_LONG``)

    返回:
        32 字符的 hex 字符串
    """
    raw = f"{decision_id}:{symbol}:{action}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
