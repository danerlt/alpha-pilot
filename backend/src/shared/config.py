"""向后兼容 shim — 新代码请从 src.configs.app_configs 导入。"""
from src.configs.app_configs import (  # noqa: F401
    AppConfig as Settings,
    InsecureSecretError,
    _looks_insecure,
    _validate_secrets,
    get_app_config as get_base_settings,
    get_settings,
)
