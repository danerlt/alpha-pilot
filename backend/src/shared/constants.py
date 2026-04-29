"""向后兼容 shim — 新代码请从 src.common.constants 导入。"""
from src.common.constants import (  # noqa: F401
    CATCHUP_LIMIT_HARD_CAP,
    DEFAULT_EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS,
    MAX_POSITION_SIZE_PCT_HARD_CAP,
)
