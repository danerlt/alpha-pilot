from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.shared.enums import TradingMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # 交易模式
    TRADING_MODE: TradingMode = TradingMode.TESTNET

    # Binance
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str

    # LLM
    LLM_PROVIDER: str = "claude"
    LLM_API_KEY: str
    LLM_MODEL: str = "claude-opus-4-6"
    LLM_TIMEOUT_SECONDS: int = 30

    # 数据库
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # 风控参数（默认值可被 .env 覆盖）
    MAX_POSITION_SIZE_PCT: float = 0.20    # 单币最大持仓占账户比例
    MAX_DAILY_LOSS_PCT: float = 0.03       # 日最大亏损占账户比例
    MAX_CONSECUTIVE_LOSSES: int = 3        # 连续亏损熔断笔数
    MAX_SINGLE_RISK_PCT: float = 0.01      # 单笔最大风险占账户比例

    # 调度参数
    STRATEGY_LOOP_INTERVAL_MINUTES: int = 15
    POSITION_MONITOR_INTERVAL_SECONDS: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
