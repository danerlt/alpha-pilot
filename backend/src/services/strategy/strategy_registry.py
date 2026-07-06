"""策略受限集注册表 (handoff 02 §P7 风控页) — 启停开关真实生效。

五个受限 strategy_mode 的展示卡片 + 启停状态。启停存 system_settings
`strategy.disabled_modes` (JSON list, 默认空=全启用); ExecutionGuard 的
strategy_enabled 规则按此拒绝被禁用模式的 OPEN_LONG (开关是真开关, 不是摆设)。
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from src.common.exception.errors import ParamsException
from src.models.audit_log import AuditLog
from src.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)

DISABLED_MODES_KEY = "strategy.disabled_modes"

# 与 proposal.py 的 strategy_mode 白名单对齐 (manual 不在受限集内, 不可禁用)
STRATEGY_CARDS = [
    {"id": "ai_trend", "name": "AI 趋势跟随", "regimes": ["trending_up"], "desc": "LLM 主导的趋势顺势开多, EMA 多头排列 + 突破确认"},
    {"id": "ai_breakout", "name": "AI 突破", "regimes": ["ranging"], "desc": "区间震荡末端的放量突破入场"},
    {"id": "ai_observation", "name": "AI 观望", "regimes": ["trending_up", "trending_down", "ranging", "chaotic"], "desc": "不满足入场条件时的显式 HOLD, 保持决策留痕"},
    {"id": "program_trend", "name": "程序化趋势", "regimes": ["trending_up"], "desc": "规则引擎趋势策略 (V0.2 预留)"},
    {"id": "program_breakout", "name": "程序化突破", "regimes": ["ranging"], "desc": "规则引擎突破策略 (V0.2 预留)"},
]

_VALID_IDS = {c["id"] for c in STRATEGY_CARDS}


def get_disabled_modes(session: Session) -> set[str]:
    row = session.query(SystemSetting).filter(
        SystemSetting.key == DISABLED_MODES_KEY,
    ).first()
    if row is None or not isinstance(row.value_json, list):
        return set()
    return {str(m) for m in row.value_json}


def list_strategies(session: Session) -> list[dict]:
    disabled = get_disabled_modes(session)
    return [
        {**card, "enabled": card["id"] not in disabled}
        for card in STRATEGY_CARDS
    ]


def set_strategy_enabled(
    session: Session, *, mode: str, enabled: bool, operator_user_id: int,
) -> dict:
    """切换启停 + 审计。本函数 commit。"""
    if mode not in _VALID_IDS:
        raise ParamsException(f"未知策略: {mode}")
    disabled = get_disabled_modes(session)
    before = sorted(disabled)
    if enabled:
        disabled.discard(mode)
    else:
        disabled.add(mode)
    row = session.query(SystemSetting).filter(
        SystemSetting.key == DISABLED_MODES_KEY,
    ).first()
    if row is None:
        row = SystemSetting(key=DISABLED_MODES_KEY, description="受限策略集启停 (风控页)")
        session.add(row)
    row.value_json = sorted(disabled)
    session.add(AuditLog(
        account_id=1, user_id=operator_user_id,
        action="strategy_toggle", resource_type="strategy", resource_id=mode,
        before_json={"disabled_modes": before},
        after_json={"disabled_modes": sorted(disabled), "enabled": enabled},
    ))
    session.commit()
    return {"ok": True}
