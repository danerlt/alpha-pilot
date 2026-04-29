"""AlphaPilot 统一配置 — 参照 Dify 项目结构，全部环境变量集中在此文件。

配置源优先级（低→高）：代码默认值 → .env 文件 → 真实环境变量。
不使用运行时远程覆盖；所有配置均从 .env 静态加载。
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.shared.enums import TradingMode

# .env 位于项目根目录（backend/src/configs/app_configs.py 上四级）。
# .resolve() 必须有：alembic 跑 env.py 时 sys.path 插入 "../" 导致
# __file__ 含未规范化的 ".." ，直接 .parent 链会算错路径。
_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"

# ── 诊断用占位符集合 ──────────────────────────────────────────────────────────
PLACEHOLDER_BINANCE_KEYS: frozenset[str] = frozenset({
    "test-binance-api-key",
    "test-binance-api-secret",
    "",
})
PLACEHOLDER_LLM_KEYS: frozenset[str] = frozenset({
    "test-llm-api-key",
    "",
})

# ── 安全校验：startup 拒绝弱/默认密钥 ─────────────────────────────────────────
_INSECURE_KEY_VALUES = frozenset({
    # 历史默认 Fernet key（已提交 git，任何能 git log 的人都能拿到）
    "2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=",
    # 当前 dev 占位 master key（base64 解码后是 "dev_test_alphapilot_key________1"）
    "ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE=",
    # 历史默认 JWT secret
    "alpha-pilot-auth-secret-change-me",
})

_INSECURE_KEY_PREFIXES = (
    "dev-only-do-not-use",
    "change-me",
    "your-secret-key",
    "test-secret",
)


class InsecureSecretError(RuntimeError):
    """AppConfig 加载时发现弱/默认密钥，必须 abort startup。"""


def _looks_insecure(value: str) -> bool:
    if not value:
        return True
    if value in _INSECURE_KEY_VALUES:
        return True
    v = value.strip().lower()
    return any(v.startswith(p.lower()) for p in _INSECURE_KEY_PREFIXES)


def _validate_secrets(settings: AppConfig) -> None:
    """Startup 安全闸：检测 SECRET / MASTER_KEY 是否仍是默认值。

    单测环境设 ALPHAPILOT_SKIP_SECRET_VALIDATION=1 跳过；生产/dev-server 不能设。
    """
    if os.getenv("ALPHAPILOT_SKIP_SECRET_VALIDATION") == "1":
        return
    insecure: list[str] = []
    if _looks_insecure(settings.APP_AUTH_SECRET_KEY):
        insecure.append("APP_AUTH_SECRET_KEY")
    if _looks_insecure(settings.APP_CONFIG_MASTER_KEY):
        insecure.append("APP_CONFIG_MASTER_KEY")
    if insecure:
        names = ", ".join(insecure)
        raise InsecureSecretError(
            f"Refusing to start: {names} 仍是默认/弱密钥。"
            f"请在 .env 提供强随机值："
            f"APP_AUTH_SECRET_KEY 用 `openssl rand -hex 32`；"
            f"APP_CONFIG_MASTER_KEY 用 "
            f"`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`。"
            f"单测请设 ALPHAPILOT_SKIP_SECRET_VALIDATION=1。"
        )


# ── 主配置类 ──────────────────────────────────────────────────────────────────
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 交易模式
    TRADING_MODE: TradingMode = TradingMode.TESTNET

    # Binance API（默认占位值仅供本地测试/健康检查；真实运行必须由 .env 覆盖）
    BINANCE_API_KEY: str = "test-binance-api-key"
    BINANCE_API_SECRET: str = "test-binance-api-secret"

    # LLM（OpenAI 兼容协议；默认指向 DeepSeek）
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = "test-llm-api-key"
    LLM_MODEL: str = "deepseek-v4-pro"
    LLM_TIMEOUT_SECONDS: int = 30

    # 数据库
    DATABASE_URL: str = "sqlite:///./alphapilot.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # 配置加密主密钥（Fernet）— 用于加密 system_settings 里 is_secret=True 的行。
    # 默认值是单测专用的"明显 dev"占位（base64 解码后是 "dev_test_alphapilot_key________1"），
    # startup 时 _validate_secrets 会拒。生产必须由 .env 提供合法 Fernet key：
    # `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
    APP_CONFIG_MASTER_KEY: str = "ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE="

    # 认证 JWT 密钥 — 同上，默认值在 startup 时被拒。生产必须由 .env 提供
    # (`openssl rand -hex 32`)。
    APP_AUTH_SECRET_KEY: str = "dev-only-do-not-use-in-prod-auth-key-please-rotate"

    # 默认管理员引导（仅在提供 env 时生效，适合 dev/test）
    DEFAULT_ADMIN_EMAIL: str = ""
    DEFAULT_ADMIN_PASSWORD: str = ""
    DEFAULT_ADMIN_USERNAME: str = ""

    # 风控参数（默认值可被 .env 覆盖）
    MAX_POSITION_SIZE_PCT: float = 0.20     # 单币最大持仓占账户比例
    MAX_DAILY_LOSS_PCT: float = 0.03        # 日最大亏损占账户比例
    MAX_CONSECUTIVE_LOSSES: int = 3         # 连续亏损熔断笔数
    MAX_SINGLE_RISK_PCT: float = 0.01       # 单笔最大风险占账户比例

    # 调度参数
    STRATEGY_LOOP_INTERVAL_MINUTES: int = 15
    POSITION_MONITOR_INTERVAL_SECONDS: int = 10

    # Pipeline feature flag（旧/新 worker 切换）
    USE_NEW_PIPELINE_WORKER: bool = False
    PIPELINE_SYMBOLS: str = "BTCUSDT,ETHUSDT"
    PIPELINE_TIMEFRAMES: str = "1h"

    # EventShuttle：一条 outbox 行 publish 失败多少次后写入 dead-letter stream
    EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS: int = 3


# ── 工厂函数 ──────────────────────────────────────────────────────────────────
@lru_cache
def get_app_config() -> AppConfig:
    s = AppConfig()
    _validate_secrets(s)
    return s


def get_settings() -> AppConfig:
    """向后兼容别名，等同于 get_app_config()。"""
    return get_app_config()


# get_base_settings 别名（部分调用点使用该名称）
get_base_settings = get_app_config


# ── 凭证诊断函数（原 config_diagnostics.py）────────────────────────────────────
def _cred_status(configured: bool, reason: str | None = None) -> dict[str, object]:
    return {"configured": configured, "reason": reason}


def get_runtime_credential_status(settings: AppConfig) -> dict[str, dict[str, object]]:
    binance_key = getattr(settings, "BINANCE_API_KEY", "") or ""
    binance_secret = getattr(settings, "BINANCE_API_SECRET", "") or ""
    llm_key = getattr(settings, "LLM_API_KEY", "") or ""

    if binance_key in PLACEHOLDER_BINANCE_KEYS or binance_secret in PLACEHOLDER_BINANCE_KEYS:
        binance = _cred_status(False, "placeholder_or_missing")
    else:
        binance = _cred_status(True, None)

    if llm_key in PLACEHOLDER_LLM_KEYS:
        llm = _cred_status(False, "placeholder_or_missing")
    else:
        llm = _cred_status(True, None)

    mode = settings.TRADING_MODE
    mode_val = mode.value if isinstance(mode, TradingMode) else str(mode)

    return {
        "binance": {**binance, "mode": mode_val},
        "llm": {
            **llm,
            "base_url": settings.LLM_BASE_URL,
            "model": settings.LLM_MODEL,
        },
    }


def can_call_binance(settings: AppConfig) -> bool:
    return bool(get_runtime_credential_status(settings)["binance"]["configured"])


def can_call_llm(settings: AppConfig) -> bool:
    return bool(get_runtime_credential_status(settings)["llm"]["configured"])
