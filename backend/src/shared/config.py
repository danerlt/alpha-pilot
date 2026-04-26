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

    # 配置加密主密钥（Fernet）— 用于加密 system_settings 里 is_secret=True 的行
    # (含 BINANCE_API_KEY/SECRET 等). 默认值是单测专用的"明显 dev"占位 (base64
    # 解码后是 "dev_test_alphapilot_key________1"), startup 时 _validate_secrets
    # 会拒. 生产必须由 .env 提供合法 Fernet key:
    # `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
    APP_CONFIG_MASTER_KEY: str = "ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE="

    # 认证 JWT 密钥 — 同上, 默认值在 startup 时被拒. 生产必须由 .env 提供
    # (`openssl rand -hex 32`).
    APP_AUTH_SECRET_KEY: str = "dev-only-do-not-use-in-prod-auth-key-please-rotate"

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

    # EventShuttle: 一条 outbox 行 publish 失败多少次后写入 dead-letter stream
    # (避免无限重试卡住整个 outbox). 设 0 / 负数等同关闭重试 (首次失败即死信).
    EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS: int = 3


# Startup 必拒的明显占位/弱密钥 (避免误将 dev key 部到生产).
# 完整字符串等值匹配 + 部分前缀匹配双管齐下.
_INSECURE_KEY_VALUES = frozenset({
    # 历史默认 Fernet key (commit 的, 任何能 git log 的人都能拿到, 必须换)
    "2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=",
    # 当前 dev 占位 master key (base64 解码后是 "dev_test_alphapilot_key________1")
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
    """Settings 加载时发现弱/默认密钥; 必须 abort startup."""


def _looks_insecure(value: str) -> bool:
    if not value:
        return True
    if value in _INSECURE_KEY_VALUES:
        return True
    v = value.strip().lower()
    return any(v.startswith(p.lower()) for p in _INSECURE_KEY_PREFIXES)


def _validate_secrets(settings: Settings) -> None:
    """Critical security gate: 启动时检测 SECRET / MASTER_KEY 是否仍是默认值.

    生产部署必须用 `.env` 提供真随机密钥 (见两个字段的 docstring 命令).
    单测环境是个例外: pytest 启动时设 ENV=test 跳过这道闸.
    """
    import os
    if os.getenv("ALPHAPILOT_SKIP_SECRET_VALIDATION") == "1":
        # 单测 / 本地 lint 用; 生产 / dev-server 不能设
        return
    insecure: list[str] = []
    if _looks_insecure(settings.APP_AUTH_SECRET_KEY):
        insecure.append("APP_AUTH_SECRET_KEY")
    if _looks_insecure(settings.APP_CONFIG_MASTER_KEY):
        insecure.append("APP_CONFIG_MASTER_KEY")
    if insecure:
        names = ", ".join(insecure)
        raise InsecureSecretError(
            f"Refusing to start: {names} 仍是默认/弱密钥. "
            f"请在 .env 提供强随机值: "
            f"APP_AUTH_SECRET_KEY 用 `openssl rand -hex 32`; "
            f"APP_CONFIG_MASTER_KEY 用 "
            f"`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`. "
            f"单测请设 ALPHAPILOT_SKIP_SECRET_VALIDATION=1."
        )


@lru_cache
def get_base_settings() -> Settings:
    s = Settings()
    _validate_secrets(s)
    return s


def get_settings() -> Settings:
    base = get_base_settings().model_dump()
    base.update(get_runtime_config_manager().get_overrides())
    return Settings(_env_file=None, **base)
