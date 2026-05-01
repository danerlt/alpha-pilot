"""AlphaPilot 统一配置 — 8 个子配置类多继承聚合。

加载优先级：代码默认 → .env 文件 → 真实环境变量。
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.shared.enums import TradingMode  # 阶段 2 会迁到 src/common/enums.py 或 src/models/enums.py

_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"


# ── 占位与安全校验（保留现有逻辑）─────────────────────────────────────────────
PLACEHOLDER_BINANCE_KEYS: frozenset[str] = frozenset(
    {"test-binance-api-key", "test-binance-api-secret", ""}
)
PLACEHOLDER_LLM_KEYS: frozenset[str] = frozenset({"test-llm-api-key", ""})

_INSECURE_KEY_VALUES = frozenset(
    {
        "2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=",
        "ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE=",
        "alpha-pilot-auth-secret-change-me",
    }
)

_INSECURE_KEY_PREFIXES = (
    "dev-only-do-not-use",
    "change-me",
    "your-secret-key",
    "test-secret",
)


class InsecureSecretError(RuntimeError):
    """启动时检测到弱/默认密钥。"""


def _looks_insecure(value: str) -> bool:
    if not value:
        return True
    if value in _INSECURE_KEY_VALUES:
        return True
    v = value.strip().lower()
    return any(v.startswith(p.lower()) for p in _INSECURE_KEY_PREFIXES)


# ── 子配置类 ───────────────────────────────────────────────────────────────
class ServiceConfig(BaseSettings):
    ENVIRONMENT: str = Field(default="dev", description="dev/uat/prod/test/local")
    LOG_LEVEL: str = Field(default="INFO")
    UVICORN_WORKER_NUM: int = Field(default=1, description="api 进程的 uvicorn worker 数")
    FASTAPI_ROOT_PATH: str = Field(default="", description="子路径部署时的 root_path（如 '/api'）")


class CORSConfig(BaseSettings):
    ENABLE_CORS: bool = Field(default=True)
    CORS_ALLOWED_ORIGINS: list[str] = Field(default=["*"])
    CORS_EXPOSE_HEADERS: list[str] = Field(default=["X-Request-ID"])


class PostgreSQLConfig(BaseSettings):
    PG_USER: str = Field(default="alphapilot")
    PG_PASSWORD: str = Field(default="alphapilot")
    PG_HOST: str = Field(default="localhost")
    PG_PORT: int = Field(default=5442)
    PG_DB: str = Field(default="alphapilot")
    POOL_SIZE: int = Field(default=20)
    POOL_MAX_OVERFLOW: int = Field(default=20)
    DB_CONNECT_TIMEOUT: int = Field(default=10)
    PRINT_SQL: bool = Field(default=False, description="echo SQL 到日志（仅 dev）")

    # 兼容性：旧代码读 DATABASE_URL；新代码用 db_uri property
    # v3.7：sqlite 占位删除；空字符串走 PG_* 拼接，仅显式 postgres:// URL 时使用
    DATABASE_URL: str = Field(
        default="",
        description="向后兼容字段；非空且 postgres:// 开头时优先用，否则按 PG_* 字段拼 db_uri",
    )

    @property
    def db_uri(self) -> str:
        """优先级：
        1. DATABASE_URL 显式设为 postgresql:// 开头时直接使用（兼容旧 .env）
        2. 否则用 PG_* 字段拼接 postgresql+psycopg2:// URI
        """
        if self.DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://", "postgres://")):
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.PG_USER}:{quote_plus(self.PG_PASSWORD)}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"
        )


class RedisConfig(BaseSettings):
    REDIS_URL: str = Field(default="redis://localhost:6389/0")


class SchedulerConfig(BaseSettings):
    STRATEGY_LOOP_INTERVAL_MINUTES: int = Field(default=15)
    POSITION_MONITOR_INTERVAL_SECONDS: int = Field(default=10)
    APSCHEDULER_JOBS_TABLE: str = Field(default="apscheduler_jobs")
    TASK_QUEUE_KEY: str = Field(default="alphapilot:tasks")
    EVENT_BUS_CHANNEL: str = Field(default="alphapilot:events")
    EVENT_SHUTTLE_BATCH_SIZE: int = Field(default=50)
    EVENT_SHUTTLE_IDLE_SLEEP_SECONDS: float = Field(default=0.5)
    EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS: int = Field(default=3)
    SCHEDULER_GRACEFUL_SHUTDOWN_SECONDS: int = Field(default=60)

    # 阶段 5 之前 lifespan 还会用现有的 strategy/position-monitor worker
    USE_NEW_PIPELINE_WORKER: bool = Field(default=False)
    PIPELINE_SYMBOLS: str = Field(default="BTCUSDT,ETHUSDT")
    PIPELINE_TIMEFRAMES: str = Field(default="1h")


class ExchangeConfig(BaseSettings):
    TRADING_MODE: TradingMode = Field(default=TradingMode.TESTNET)
    BINANCE_API_KEY: str = Field(default="test-binance-api-key")
    BINANCE_API_SECRET: str = Field(default="test-binance-api-secret")


class LLMConfig(BaseSettings):
    LLM_BASE_URL: str = Field(default="https://api.deepseek.com/v1")
    LLM_API_KEY: str = Field(default="test-llm-api-key")
    LLM_MODEL: str = Field(default="deepseek-v4-pro")
    LLM_TIMEOUT_SECONDS: int = Field(default=30)


class RiskConfig(BaseSettings):
    MAX_POSITION_SIZE_PCT: float = Field(default=0.20)
    MAX_DAILY_LOSS_PCT: float = Field(default=0.03)
    MAX_CONSECUTIVE_LOSSES: int = Field(default=3)
    MAX_SINGLE_RISK_PCT: float = Field(default=0.01)


class SecurityConfig(BaseSettings):
    APP_CONFIG_MASTER_KEY: str = Field(default="ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE=")
    APP_AUTH_SECRET_KEY: str = Field(default="dev-only-do-not-use-in-prod-auth-key-please-rotate")
    DEFAULT_ADMIN_EMAIL: str = Field(default="")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="")
    DEFAULT_ADMIN_USERNAME: str = Field(default="")


# ── 主配置（多继承聚合）─────────────────────────────────────────────────────
class AppConfig(
    ServiceConfig,
    CORSConfig,
    PostgreSQLConfig,
    RedisConfig,
    SchedulerConfig,
    ExchangeConfig,
    LLMConfig,
    RiskConfig,
    SecurityConfig,
):
    """全局应用配置。业务代码通过 ``get_app_config().FIELD`` 访问。"""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


def _validate_secrets(settings: AppConfig) -> None:
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
            "APP_AUTH_SECRET_KEY 用 `openssl rand -hex 32`；"
            'APP_CONFIG_MASTER_KEY 用 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`。'
            "单测请设 ALPHAPILOT_SKIP_SECRET_VALIDATION=1。"
        )


@lru_cache
def get_app_config() -> AppConfig:
    s = AppConfig()
    _validate_secrets(s)
    return s


def get_settings() -> AppConfig:
    """向后兼容别名。"""
    return get_app_config()


get_base_settings = get_app_config


# ── 凭证诊断（保留现有 API）────────────────────────────────────────────────
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
        "llm": {**llm, "base_url": settings.LLM_BASE_URL, "model": settings.LLM_MODEL},
    }


def can_call_binance(settings: AppConfig) -> bool:
    return bool(get_runtime_credential_status(settings)["binance"]["configured"])


def can_call_llm(settings: AppConfig) -> bool:
    return bool(get_runtime_credential_status(settings)["llm"]["configured"])
