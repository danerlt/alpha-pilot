"""统一错误码枚举。

段位约定：
- "0"          成功
- "400xxx"     客户端错误（参数 / 认证 / 找不到 / 限流 / 冲突）
- "500xxx"     服务端错误（系统 / 服务层 / DB / Redis）
- "600xxx"     alpha-pilot 业务专属错误码
"""
from __future__ import annotations

from enum import Enum


class ErrorCode(Enum):
    SUCCESS = ("0", "成功")

    # 客户端错误 4xxxxx
    PARAM_ERROR = ("400001", "参数错误")
    VALIDATION_ERROR = ("400002", "参数校验失败")
    AUTH_ERROR = ("400003", "认证失败")
    FORBIDDEN = ("400004", "权限不足")
    NOT_FOUND = ("400005", "资源不存在")
    RATE_LIMIT = ("400006", "请求过于频繁")
    CONFLICT = ("400009", "资源冲突")

    # 服务端错误 5xxxxx
    SYS_ERROR = ("500001", "系统错误")
    SERVICE_ERROR = ("500002", "服务层错误")
    DB_ERROR = ("500003", "数据库错误")
    REDIS_ERROR = ("500006", "Redis 错误")

    # alpha-pilot 业务专属 6xxxxx
    KILL_SWITCH_PAUSED = ("600001", "系统紧急停机中")
    RISK_REJECTED = ("600002", "风控校验未通过")
    IDEMPOTENCY_CONFLICT = ("600003", "幂等键冲突")
    INSUFFICIENT_BALANCE = ("600004", "账户余额不足")
    EXCHANGE_API_ERROR = ("600005", "交易所接口异常")
    LLM_RESPONSE_INVALID = ("600006", "LLM 响应格式异常")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def msg(self) -> str:
        return self.value[1]
