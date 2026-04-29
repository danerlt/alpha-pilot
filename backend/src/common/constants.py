"""AlphaPilot 默认常量集中地。

只放跨模块共享、且不该走 .env 配置的"硬上限"——
设计上是不可被运行时配置突破的安全闸门，而非用户可调参数。

各模块 `from src.common.constants import X` 取值，不再各自 hard-code。
"""
from __future__ import annotations

# 仓位上限硬闸门 — 即使 LLM 给出 0.99，DecisionSolver 也会拒收。
# spec §1.4：V0.1 单币最多 20% 账户余额。
MAX_POSITION_SIZE_PCT_HARD_CAP: float = 0.20

# 事件 catchup 最大单次拉取行数 — 客户端断线长（>200 条）时分页拉。
CATCHUP_LIMIT_HARD_CAP: int = 500

# EventShuttle 死信阈值默认值 — 实际值由 settings.EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS
# 覆盖，这里只是兜底。0 / 负数 = 首次失败即死信。
DEFAULT_EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS: int = 3
