from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.shared.enums import TradingMode
from src.shared.runtime_config import get_runtime_config_manager

# .env 位于项目根目录（backend/src/shared/config.py 上三级）
_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # 交易模式
    TRADING_MODE: TradingMode = TradingMode.TESTNET

    # Binance
    # 默认占位值用于本地测试 / 健康检查；真实运行必须由 .env 覆盖
    BINANCE_API_KEY: str = "test-binance-api-key"
    BINANCE_API_SECRET: str = "test-binance-api-secret"

    # LLM
    LLM_PROVIDER: str = "claude"
    LLM_API_KEY: str = "test-llm-api-key"
    LLM_MODEL: str = "claude-opus-4-6"
    LLM_TIMEOUT_SECONDS: int = 30

    # 数据库
    DATABASE_URL: str = "sqlite:///./alphapilot.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # 配置加密主密钥（Fernet）
    APP_CONFIG_MASTER_KEY: str = "2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA="

    # 认证 JWT 密钥
    APP_AUTH_SECRET_KEY: str = "alpha-pilot-auth-secret-change-me"

    # 默认管理员引导（仅在提供 env 时生效，适合 dev/test）
    DEFAULT_ADMIN_EMAIL: str = ""
    DEFAULT_ADMIN_PASSWORD: str = ""
    DEFAULT_ADMIN_USERNAME: str = ""

    # 风控参数（默认值可被 .env 覆盖）
    MAX_POSITION_SIZE_PCT: float = 0.20    # 单币最大持仓占账户比例
    MAX_DAILY_LOSS_PCT: float = 0.03       # 日最大亏损占账户比例
    MAX_CONSECUTIVE_LOSSES: int = 3        # 连续亏损熔断笔数
    MAX_SINGLE_RISK_PCT: float = 0.01      # 单笔最大风险占账户比例

    # 调度参数
    STRATEGY_LOOP_INTERVAL_MINUTES: int = 15
    POSITION_MONITOR_INTERVAL_SECONDS: int = 10

    # Pipeline feature flag (Plan 2 → Plan 5 渐进切换)
    # USE_NEW_PIPELINE_WORKER=true 启用 src/workers/strategy_pipeline.py 新 worker;
    # false (默认) 保留旧 src/workers/strategy_loop.py 不动。
    USE_NEW_PIPELINE_WORKER: bool = False
    PIPELINE_SYMBOLS: str = "BTCUSDT,ETHUSDT"
    PIPELINE_TIMEFRAMES: str = "1h"


@lru_cache
def get_base_settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    base = get_base_settings().model_dump()
    base.update(get_runtime_config_manager().get_overrides())
    return Settings(_env_file=None, **base)
