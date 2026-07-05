"""权限矩阵常量 (handoff/03 §3.7 + webapp 架构 B3)。

硬编码为常量表: 前端 usePermission() 的唯一数据源 (前端不留第二份真相)。
当前用户体系只有 user/admin 两角色, ROLE_ALIASES 把 legacy "user" 映射为
"trader" 做 UI 展示; 端点级强制仍走 require_admin, P4 RBAC 落地后本表
接入 require_permission 依赖项成为真正的守卫来源。
"""
from __future__ import annotations

ROLES = ["owner", "admin", "trader", "viewer"]

# P4 RBAC 前的过渡映射 (users.role 现值 → 矩阵角色)
ROLE_ALIASES = {"user": "trader"}

# 与设计稿 admin.jsx PERMS 逐项对齐 (交易/策略/系统三组)
PERMISSION_MATRIX = [
    {
        "group": "交易",
        "items": [
            {"key": "trade.view", "label": "查看持仓与行情", "owner": True, "admin": True, "trader": True, "viewer": True},
            {"key": "trade.manual_order", "label": "手动下单 / 平仓", "owner": True, "admin": True, "trader": True, "viewer": False},
            {"key": "trade.engine_toggle", "label": "启停自动交易", "owner": True, "admin": True, "trader": True, "viewer": False},
            {"key": "risk.edit_hard_limits", "label": "修改硬风控阈值", "owner": True, "admin": True, "trader": False, "viewer": False},
        ],
    },
    {
        "group": "策略",
        "items": [
            {"key": "lab.view", "label": "查看策略与实验室", "owner": True, "admin": True, "trader": True, "viewer": True},
            {"key": "lab.submit_candidate", "label": "提交策略候选", "owner": True, "admin": True, "trader": True, "viewer": False},
            {"key": "lab.approve_promote", "label": "批准灰度 / 上线", "owner": True, "admin": True, "trader": False, "viewer": False},
        ],
    },
    {
        "group": "系统",
        "items": [
            {"key": "system.exchange_config", "label": "交易所 API 配置", "owner": True, "admin": True, "trader": False, "viewer": False},
            {"key": "system.llm_config", "label": "LLM 模型配置", "owner": True, "admin": True, "trader": False, "viewer": False},
            {"key": "system.user_management", "label": "用户与权限管理", "owner": True, "admin": True, "trader": False, "viewer": False},
            {"key": "system.emergency_stop", "label": "紧急停止引擎", "owner": True, "admin": True, "trader": True, "viewer": False},
        ],
    },
]


def resolve_role(raw_role: str) -> str:
    """users.role 现值 → 矩阵角色 (legacy 'user' → 'trader')。"""
    return ROLE_ALIASES.get(raw_role, raw_role)
