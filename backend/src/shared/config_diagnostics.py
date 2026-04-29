"""向后兼容 shim — 新代码请从 src.configs.app_configs 导入。"""
from src.configs.app_configs import (  # noqa: F401
    AppConfig as Settings,
    can_call_binance,
    can_call_llm,
    get_runtime_credential_status,
    PLACEHOLDER_BINANCE_KEYS,
    PLACEHOLDER_LLM_KEYS,
)
