"""事件 → 通知消息映射 (PRD P1 通知系统)。

format_notification(envelope) 把 EventEnvelope 映射成 NotificationMessage;
非告警事件 (不在白名单) 返回 None。severity 三档: info < warn < critical。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.services.events.contracts import EventEnvelope

_SEVERITY_ORDER = {"info": 0, "warn": 1, "critical": 2}


def severity_rank(severity: str) -> int:
    """severity 排序值, 未知按最低 (info) 处理。"""
    return _SEVERITY_ORDER.get(severity, 0)


@dataclass(frozen=True)
class NotificationMessage:
    event_id: str
    event_type: str
    severity: str  # info | warn | critical
    title: str
    body: str
    trading_mode: str


def _mode_tag(envelope: EventEnvelope) -> str:
    return envelope.trading_mode.upper()


# ── 各事件类型的 formatter (payload -> (severity, title, body)) ──────────────

def _fmt_circuit_breaker(env: EventEnvelope) -> tuple[str, str, str]:
    reason = env.payload.get("reason", "unknown")
    return "critical", f"🔴 [{_mode_tag(env)}] 风控熔断触发", f"原因: {reason}"


def _fmt_risk_event(env: EventEnvelope) -> tuple[str, str, str]:
    p = env.payload
    severity = p.get("severity", "warn")
    icon = {"critical": "🔴", "warn": "🟠", "info": "🟢"}.get(severity, "🟠")
    symbol = p.get("symbol") or "-"
    return (
        severity,
        f"{icon} [{_mode_tag(env)}] 风控事件 {p.get('event_subtype', '')}",
        f"子类型: {p.get('event_subtype', '')} | 标的: {symbol} | 事件ID: {p.get('risk_event_id')}",
    )


def _fmt_order_failed(env: EventEnvelope) -> tuple[str, str, str]:
    p = env.payload
    return (
        "warn",
        f"🟠 [{_mode_tag(env)}] 订单失败",
        f"订单ID: {p.get('order_id')} | 原因: {p.get('reason', 'unknown')}",
    )


def _fmt_position_opened(env: EventEnvelope) -> tuple[str, str, str]:
    p = env.payload
    return (
        "info",
        f"🟢 [{_mode_tag(env)}] 开仓 {p.get('symbol', '')}",
        f"数量: {p.get('quantity')} @ {p.get('entry_price')} | 止损: {p.get('stop_loss')}",
    )


def _fmt_position_closed(env: EventEnvelope) -> tuple[str, str, str]:
    p = env.payload
    return (
        "info",
        f"⚪ [{_mode_tag(env)}] 平仓",
        f"持仓ID: {p.get('position_id')} @ {p.get('exit_price')} | 原因: {p.get('exit_reason', '')}",
    )


def _fmt_trade_closed(env: EventEnvelope) -> tuple[str, str, str]:
    p = env.payload
    pnl = p.get("pnl", 0.0)
    icon = "🟢" if (pnl or 0) >= 0 else "🔴"
    pct = (p.get("pnl_pct", 0.0) or 0.0) * 100
    return (
        "info",
        f"{icon} [{_mode_tag(env)}] 交易了结 {p.get('symbol', '')}",
        f"盈亏: {pnl} ({pct:.2f}%) | 原因: {p.get('exit_reason', '')}",
    )


def _fmt_manual_override(env: EventEnvelope) -> tuple[str, str, str]:
    p = env.payload
    return (
        "warn",
        f"🟠 [{_mode_tag(env)}] 手动操作",
        f"操作: {p.get('action')} | 目标: {p.get('target')} | 操作人: {p.get('operator_user_id')} | 原因: {p.get('reason', '')}",
    )


# 告警事件白名单 (未注册的事件类型 → 不告警)
_FORMATTERS: dict[str, Callable[[EventEnvelope], tuple[str, str, str]]] = {
    "circuit_breaker.triggered": _fmt_circuit_breaker,
    "risk.event.triggered": _fmt_risk_event,
    "order.failed": _fmt_order_failed,
    "position.opened": _fmt_position_opened,
    "position.closed": _fmt_position_closed,
    "trade.closed": _fmt_trade_closed,
    "manual.override": _fmt_manual_override,
}

ALERT_EVENT_TYPES: frozenset[str] = frozenset(_FORMATTERS.keys())


def format_notification(envelope: EventEnvelope) -> NotificationMessage | None:
    """映射告警事件为通知消息; 非白名单事件返回 None。"""
    formatter = _FORMATTERS.get(envelope.event_type)
    if formatter is None:
        return None
    severity, title, body = formatter(envelope)
    return NotificationMessage(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        severity=severity,
        title=title,
        body=body,
        trading_mode=envelope.trading_mode,
    )
