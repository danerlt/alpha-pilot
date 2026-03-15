# AlphaPilot Plan 1: Project Foundation

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建完整的项目脚手架，包含 Docker Compose 环境、PostgreSQL 数据库模型、Alembic 迁移、FastAPI 骨架服务和 Makefile 统一入口，交付一个可启动并通过健康检查的后端服务。

**Architecture:** Monorepo 结构，`backend/` 包含所有 Python 代码（`src/`+`tests/`+`migrations/`），`docker/` 管理容器编排，根目录 `Makefile` 作为统一命令入口。FastAPI 使用 `pydantic-settings` 管理配置，SQLAlchemy 2.x + Alembic 管理数据库。

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16, Redis 7, Docker Compose, uv (包管理), pytest

---

## Chunk 1: 项目脚手架（目录结构 + 依赖 + Docker）

### Task 1: 创建目录结构和 pyproject.toml

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/src/__init__.py`
- Create: `backend/src/app/__init__.py`
- Create: `backend/src/shared/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/unit/__init__.py`
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/api/__init__.py`
- Create: `backend/scripts/.gitkeep`

- [ ] **Step 1: 创建后端目录结构**

```bash
mkdir -p backend/src/app
mkdir -p backend/src/shared/models
mkdir -p backend/src/shared/schemas
mkdir -p backend/tests/unit
mkdir -p backend/tests/integration
mkdir -p backend/tests/api
mkdir -p backend/scripts
mkdir -p backend/migrations/versions
mkdir -p frontend
mkdir -p docker
```

- [ ] **Step 2: 创建所有 `__init__.py` 文件**

```bash
touch backend/src/__init__.py
touch backend/src/app/__init__.py
touch backend/src/shared/__init__.py
touch backend/src/shared/models/__init__.py
touch backend/src/shared/schemas/__init__.py
touch backend/tests/__init__.py
touch backend/tests/unit/__init__.py
touch backend/tests/integration/__init__.py
touch backend/tests/api/__init__.py
```

- [ ] **Step 3: 创建 `backend/pyproject.toml`**

```toml
[project]
name = "alpha-pilot-backend"
version = "0.1.0"
description = "AlphaPilot AI Trading System Backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.14.0",
    "psycopg2-binary>=2.9.10",
    "redis>=5.2.0",
    "apscheduler>=3.10.4",
    "httpx>=0.28.0",
    "python-binance>=1.0.19",
    "pandas>=2.2.0",
    "pandas-ta>=0.3.14b",
    "anthropic>=0.40.0",
    "openai>=1.58.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "testcontainers[postgres,redis]>=4.8.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

- [ ] **Step 4: 在 `backend/` 目录安装依赖**

```bash
cd backend
pip install uv  # 若未安装
uv venv .venv
source .venv/bin/activate   # Linux/Mac/Cygwin
uv pip install -e ".[dev]"
```

Expected: 所有依赖安装成功，无错误。

- [ ] **Step 5: 提交**

```bash
git add backend/
git commit -m "feat: init backend project structure and dependencies"
```

---

### Task 2: 创建 Docker Compose 环境

**Files:**
- Create: `docker/docker-compose.yml`
- Create: `docker/docker-compose.dev.yml`
- Create: `docker/Dockerfile.backend`
- Create: `.env.example`
- Create: `.env` (本地使用，gitignore)
- Create: `.gitignore`

- [ ] **Step 1: 创建 `.gitignore`**

```
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
backend/.venv/
backend/dist/
backend/*.egg-info/
frontend/node_modules/
frontend/.next/
```

- [ ] **Step 2: 创建 `.env.example`**

```env
# 交易模式: testnet | mainnet
TRADING_MODE=testnet

# Binance API
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# LLM 配置
LLM_PROVIDER=claude
LLM_API_KEY=your_llm_api_key
LLM_MODEL=claude-opus-4-6
LLM_TIMEOUT_SECONDS=30

# 数据库
DATABASE_URL=postgresql://alphapilot:alphapilot@localhost:5432/alphapilot

# Redis
REDIS_URL=redis://localhost:6379/0

# 风控默认参数
MAX_POSITION_SIZE_PCT=0.20
MAX_DAILY_LOSS_PCT=0.03
MAX_CONSECUTIVE_LOSSES=3
MAX_SINGLE_RISK_PCT=0.01

# APScheduler
STRATEGY_LOOP_INTERVAL_MINUTES=15
POSITION_MONITOR_INTERVAL_SECONDS=10
```

- [ ] **Step 3: 创建 `.env`（复制 example 并填写本地值）**

```bash
cp .env.example .env
# 编辑 .env 填入实际值（Testnet 环境）
```

- [ ] **Step 4: 创建 `docker/Dockerfile.backend`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml .

# 安装依赖
RUN uv pip install --system -e ".[dev]"

# 复制源码
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini .
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 5: 创建 `docker/docker-compose.yml`（生产用）**

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: alphapilot
      POSTGRES_PASSWORD: alphapilot
      POSTGRES_DB: alphapilot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alphapilot"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    env_file:
      - ../.env
    environment:
      DATABASE_URL: postgresql://alphapilot:alphapilot@postgres:5432/alphapilot
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
```

- [ ] **Step 6: 创建 `docker/docker-compose.dev.yml`（开发用，挂载源码热重载）**

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: alphapilot
      POSTGRES_PASSWORD: alphapilot
      POSTGRES_DB: alphapilot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alphapilot"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

> 开发时后端在本地直接运行（`make dev-backend`），只用 Docker 跑 postgres 和 redis。

- [ ] **Step 7: 启动开发环境验证**

```bash
cd docker
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps
```

Expected: postgres 和 redis 均为 healthy 状态。

- [ ] **Step 8: 提交**

```bash
git add docker/ .env.example .gitignore
git commit -m "feat: add Docker Compose dev environment"
```

---

### Task 3: 创建 Makefile 统一入口

**Files:**
- Create: `Makefile`

- [ ] **Step 1: 创建根目录 `Makefile`**

```makefile
.PHONY: help dev-up dev-down init-db upgrade-db test test-unit test-integration lint fmt

DOCKER_DEV = docker compose -f docker/docker-compose.dev.yml
BACKEND = cd backend && source .venv/bin/activate &&

help:
	@echo "AlphaPilot Development Commands"
	@echo ""
	@echo "  make dev-up          Start dev infrastructure (postgres, redis)"
	@echo "  make dev-down        Stop dev infrastructure"
	@echo "  make dev-backend     Start FastAPI backend (hot reload)"
	@echo "  make init-db         Initialize database schema"
	@echo "  make upgrade-db      Run pending Alembic migrations"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make lint            Run ruff linter"
	@echo "  make fmt             Run ruff formatter"

dev-up:
	$(DOCKER_DEV) up -d

dev-down:
	$(DOCKER_DEV) down

dev-backend:
	cd backend && source .venv/bin/activate && uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

init-db:
	cd backend && source .venv/bin/activate && python scripts/init_db.py

upgrade-db:
	cd backend && source .venv/bin/activate && python scripts/upgrade_db.py

test:
	cd backend && source .venv/bin/activate && pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	cd backend && source .venv/bin/activate && pytest tests/unit/ -v

test-integration:
	cd backend && source .venv/bin/activate && pytest tests/integration/ -v

lint:
	cd backend && source .venv/bin/activate && ruff check src/ tests/

fmt:
	cd backend && source .venv/bin/activate && ruff format src/ tests/
```

- [ ] **Step 2: 验证 Makefile 帮助命令**

```bash
make help
```

Expected: 打印所有可用命令列表。

- [ ] **Step 3: 提交**

```bash
git add Makefile
git commit -m "feat: add Makefile with dev commands"
```

---

## Chunk 2: 配置、枚举与 FastAPI 骨架

### Task 4: 共享配置和枚举

**Files:**
- Create: `backend/src/shared/config.py`
- Create: `backend/src/shared/enums.py`
- Test: `backend/tests/unit/test_config.py`

- [ ] **Step 1: 先写失败测试 `backend/tests/unit/test_config.py`**

```python
import pytest
from src.shared.config import Settings
from src.shared.enums import TradingMode, Action, EntryType, StrategyMode, RegimeType, GuardResult


def test_settings_defaults():
    s = Settings(
        BINANCE_API_KEY="key",
        BINANCE_API_SECRET="secret",
        LLM_API_KEY="llmkey",
        DATABASE_URL="postgresql://user:pass@localhost/db",
        REDIS_URL="redis://localhost:6379/0",
    )
    assert s.TRADING_MODE == TradingMode.TESTNET
    assert s.LLM_TIMEOUT_SECONDS == 30
    assert s.MAX_POSITION_SIZE_PCT == 0.20
    assert s.MAX_DAILY_LOSS_PCT == 0.03
    assert s.MAX_CONSECUTIVE_LOSSES == 3
    assert s.MAX_SINGLE_RISK_PCT == 0.01


def test_trading_mode_enum():
    assert TradingMode.TESTNET.value == "testnet"
    assert TradingMode.MAINNET.value == "mainnet"


def test_action_enum():
    assert Action.OPEN_LONG.value == "OPEN_LONG"
    assert Action.CLOSE_LONG.value == "CLOSE_LONG"
    assert Action.HOLD.value == "HOLD"
    # V0.1 仅做多，不应有 OPEN_SHORT
    assert not hasattr(Action, "OPEN_SHORT")


def test_guard_result_enum():
    assert GuardResult.PASS.value == "PASS"
    assert GuardResult.REJECT.value == "REJECT"
    assert GuardResult.DEGRADE.value == "DEGRADE"


def test_regime_type_enum():
    assert RegimeType.TRENDING_UP.value == "trending_up"
    assert RegimeType.TRENDING_DOWN.value == "trending_down"
    assert RegimeType.RANGING.value == "ranging"
    assert RegimeType.CHAOTIC.value == "chaotic"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && source .venv/bin/activate
pytest tests/unit/test_config.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`（模块还未创建）

- [ ] **Step 3: 创建 `backend/src/shared/enums.py`**

```python
from enum import Enum


class TradingMode(str, Enum):
    TESTNET = "testnet"
    MAINNET = "mainnet"


class Action(str, Enum):
    OPEN_LONG = "OPEN_LONG"
    CLOSE_LONG = "CLOSE_LONG"
    HOLD = "HOLD"
    # V0.1 不支持做空（OPEN_SHORT / CLOSE_SHORT 在 V0.3+ 支持）


class EntryType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class StrategyMode(str, Enum):
    TREND_FOLLOWING = "trend_following"
    BREAKOUT = "breakout"
    OBSERVATION = "observation"


class RegimeType(str, Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    CHAOTIC = "chaotic"


class GuardResult(str, Enum):
    PASS = "PASS"
    REJECT = "REJECT"
    DEGRADE = "DEGRADE"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class TradeExitReason(str, Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    AI_CLOSE = "ai_close"
    MANUAL_CLOSE = "manual_close"
    CIRCUIT_BREAKER = "circuit_breaker"
    PARTIAL = "partial"
```

- [ ] **Step 4: 创建 `backend/src/shared/config.py`**

```python
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
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd backend && source .venv/bin/activate
pytest tests/unit/test_config.py -v
```

Expected: 所有 5 个测试 PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/shared/enums.py backend/src/shared/config.py backend/tests/unit/test_config.py
git commit -m "feat: add shared enums and pydantic-settings config"
```

---

### Task 5: FastAPI 应用骨架

**Files:**
- Create: `backend/src/app/main.py`
- Create: `backend/src/app/router.py`
- Test: `backend/tests/api/test_health.py`

- [ ] **Step 1: 先写失败测试 `backend/tests/api/test_health.py`**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "trading_mode" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root_redirect():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code in (200, 307, 308)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && source .venv/bin/activate
pytest tests/api/test_health.py -v
```

Expected: `ImportError`（main.py 未创建）

- [ ] **Step 3: 创建 `backend/src/app/router.py`**

```python
from fastapi import APIRouter
from src.shared.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "trading_mode": settings.TRADING_MODE.value,
        "version": "0.1.0",
    }
```

- [ ] **Step 4: 创建 `backend/src/app/main.py`**

```python
from fastapi import FastAPI
from src.app.router import router

app = FastAPI(
    title="AlphaPilot API",
    description="AI Autonomous Trading System",
    version="0.1.0",
)

app.include_router(router)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd backend && source .venv/bin/activate
pytest tests/api/test_health.py -v
```

Expected: 2 个测试 PASS

- [ ] **Step 6: 手动启动验证**

```bash
make dev-up  # 启动 postgres 和 redis
make dev-backend  # 启动 FastAPI
# 在新终端：
curl http://localhost:8000/health
```

Expected: `{"status":"ok","trading_mode":"testnet","version":"0.1.0"}`

- [ ] **Step 7: 提交**

```bash
git add backend/src/app/ backend/tests/api/test_health.py
git commit -m "feat: add FastAPI app skeleton with health check endpoint"
```

---

## Chunk 3: 数据库模型与 Alembic 迁移

### Task 6: SQLAlchemy 数据库连接

**Files:**
- Create: `backend/src/shared/db.py`
- Create: `backend/src/shared/models/base.py`
- Test: `backend/tests/integration/test_db.py`

- [ ] **Step 1: 创建 `backend/src/shared/models/base.py`**

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """所有表的创建/更新时间基类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [ ] **Step 2: 创建 `backend/src/shared/db.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.shared.config import get_settings

# 模块级单例，确保连接池只创建一次
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        # SQLAlchemy 2.x: engine 作为第一个位置参数，不用 bind=
        _SessionLocal = sessionmaker(get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_db() -> Session:
    """FastAPI 依赖注入用"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: 先写失败集成测试 `backend/tests/integration/test_db.py`**

```python
import pytest
from sqlalchemy import text, create_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def postgres_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()


def test_db_connection(postgres_url):
    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_db_ping(postgres_url):
    engine = create_engine(postgres_url, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        assert "PostgreSQL" in version
```

- [ ] **Step 4: 运行集成测试**

```bash
cd backend && source .venv/bin/activate
pytest tests/integration/test_db.py -v
```

Expected: 2 个测试 PASS（testcontainers 自动拉起 postgres）

- [ ] **Step 5: 提交**

```bash
git add backend/src/shared/db.py backend/src/shared/models/base.py backend/tests/integration/test_db.py
git commit -m "feat: add SQLAlchemy db connection and base model"
```

---

### Task 7: 所有数据库模型

**Files:**
- Create: `backend/src/shared/models/candle.py`
- Create: `backend/src/shared/models/account.py`
- Create: `backend/src/shared/models/indicator.py`
- Create: `backend/src/shared/models/regime.py`
- Create: `backend/src/shared/models/position.py`
- Create: `backend/src/shared/models/decision.py`
- Create: `backend/src/shared/models/order.py`
- Create: `backend/src/shared/models/trade.py`
- Create: `backend/src/shared/models/risk_event.py`
- Create: `backend/src/shared/models/experience.py`
- Create: `backend/src/shared/models/report.py`
- Modify: `backend/src/shared/models/__init__.py`
- Test: `backend/tests/unit/test_models.py`

- [ ] **Step 1: 先写失败测试 `backend/tests/unit/test_models.py`**

```python
from src.shared.models import (
    Candle, AccountSnapshot, IndicatorSnapshot,
    RegimeSnapshot, Position, AIDecision,
    Order, Trade, RiskEvent, ExperienceRecord, DailyReport
)
from src.shared.enums import TradingMode


def test_all_models_importable():
    """所有模型可正常导入"""
    assert Candle.__tablename__ == "candles"
    assert AccountSnapshot.__tablename__ == "account_snapshots"
    assert IndicatorSnapshot.__tablename__ == "indicator_snapshots"
    assert RegimeSnapshot.__tablename__ == "regime_snapshots"
    assert Position.__tablename__ == "positions"
    assert AIDecision.__tablename__ == "ai_decisions"
    assert Order.__tablename__ == "orders"
    assert Trade.__tablename__ == "trades"
    assert RiskEvent.__tablename__ == "risk_events"
    assert ExperienceRecord.__tablename__ == "experience_store"
    assert DailyReport.__tablename__ == "daily_reports"


def test_trading_mode_column_exists():
    """所有表含 trading_mode 列（testnet/mainnet 数据完全隔离）"""
    for model in [
        Candle, AccountSnapshot, IndicatorSnapshot, RegimeSnapshot,
        Position, AIDecision, Order, Trade, RiskEvent, ExperienceRecord, DailyReport,
    ]:
        assert hasattr(model, "trading_mode"), f"{model.__name__} missing trading_mode"
```

- [ ] **Step 2: 创建 `backend/src/shared/models/candle.py`**

```python
from datetime import datetime
from sqlalchemy import String, BigInteger, Numeric, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode


class Candle(Base, TimestampMixin):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)  # 15m, 1h
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(30, 8), nullable=False)

    __table_args__ = (
        Index("ix_candles_symbol_timeframe_open_time", "symbol", "timeframe", "open_time", unique=True),
    )
```

- [ ] **Step 3: 创建 `backend/src/shared/models/account.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode


class AccountSnapshot(Base, TimestampMixin):
    __tablename__ = "account_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_balance_usdt: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    available_balance_usdt: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    daily_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    daily_pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0)
```

- [ ] **Step 4: 创建 `backend/src/shared/models/indicator.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode


class IndicatorSnapshot(Base, TimestampMixin):
    __tablename__ = "indicator_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ema20: Mapped[float | None] = mapped_column(Numeric(20, 8))
    ema50: Mapped[float | None] = mapped_column(Numeric(20, 8))
    ema200: Mapped[float | None] = mapped_column(Numeric(20, 8))
    rsi: Mapped[float | None] = mapped_column(Numeric(10, 4))
    macd: Mapped[float | None] = mapped_column(Numeric(20, 8))
    macd_signal: Mapped[float | None] = mapped_column(Numeric(20, 8))
    macd_hist: Mapped[float | None] = mapped_column(Numeric(20, 8))
    atr: Mapped[float | None] = mapped_column(Numeric(20, 8))
    bb_upper: Mapped[float | None] = mapped_column(Numeric(20, 8))
    bb_middle: Mapped[float | None] = mapped_column(Numeric(20, 8))
    bb_lower: Mapped[float | None] = mapped_column(Numeric(20, 8))
    volume_ma: Mapped[float | None] = mapped_column(Numeric(30, 8))
    volatility: Mapped[float | None] = mapped_column(Numeric(10, 6))
    extra: Mapped[dict | None] = mapped_column(JSON)  # 额外指标扩展
```

- [ ] **Step 5: 创建 `backend/src/shared/models/regime.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import RegimeType, TradingMode


class RegimeSnapshot(Base, TimestampMixin):
    __tablename__ = "regime_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    regime: Mapped[str] = mapped_column(String(20), nullable=False)  # RegimeType value
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    features: Mapped[dict | None] = mapped_column(JSON)  # 识别所用特征值
```

- [ ] **Step 6: 创建 `backend/src/shared/models/position.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode, PositionStatus


class Position(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=PositionStatus.OPEN.value)
    side: Mapped[str] = mapped_column(String(10), nullable=False, default="LONG")  # V0.1 仅 LONG
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    stop_loss: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    take_profit: Mapped[float | None] = mapped_column(Numeric(20, 8))
    current_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    unrealized_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8))
    unrealized_pnl_pct: Mapped[float | None] = mapped_column(Numeric(10, 6))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_decision_id: Mapped[int | None] = mapped_column(BigInteger)
```

- [ ] **Step 7: 创建 `backend/src/shared/models/decision.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode, Action


class AIDecision(Base, TimestampMixin):
    __tablename__ = "ai_decisions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # Action value
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    entry_type: Mapped[str | None] = mapped_column(String(10))
    entry_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    stop_loss: Mapped[float | None] = mapped_column(Numeric(20, 8))
    take_profit: Mapped[float | None] = mapped_column(Numeric(20, 8))
    position_size_pct: Mapped[float | None] = mapped_column(Numeric(5, 4))
    strategy_mode: Mapped[str | None] = mapped_column(String(30))
    reasoning: Mapped[list | None] = mapped_column(JSON)
    risk_note: Mapped[str | None] = mapped_column(Text)
    prompt_input: Mapped[dict | None] = mapped_column(JSON)   # 完整 prompt 输入（审计用）
    raw_output: Mapped[str | None] = mapped_column(Text)      # LLM 原始输出（审计用）
    is_fallback: Mapped[bool] = mapped_column(nullable=False, default=False)  # 是否触发兜底 HOLD
```

- [ ] **Step 8: 创建 `backend/src/shared/models/order.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode, OrderStatus


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # 幂等 key
    binance_order_id: Mapped[str | None] = mapped_column(String(50))
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)   # BUY / SELL
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)  # MARKET / LIMIT / STOP_LOSS
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    filled_quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    avg_fill_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=OrderStatus.PENDING.value)
    position_id: Mapped[int | None] = mapped_column(BigInteger)
    ai_decision_id: Mapped[int | None] = mapped_column(BigInteger)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(500))
```

- [ ] **Step 9: 创建 `backend/src/shared/models/trade.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger, Interval
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode, TradeExitReason


class Trade(Base, TimestampMixin):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    position_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False, default="LONG")
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    exit_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    exit_reason: Mapped[str] = mapped_column(String(30), nullable=False)  # TradeExitReason value
    strategy_mode: Mapped[str | None] = mapped_column(String(30))
    regime: Mapped[str | None] = mapped_column(String(20))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    holding_seconds: Mapped[int | None] = mapped_column(BigInteger)
    ai_decision_id: Mapped[int | None] = mapped_column(BigInteger)
    open_order_id: Mapped[int | None] = mapped_column(BigInteger)
    close_order_id: Mapped[int | None] = mapped_column(BigInteger)
```

- [ ] **Step 10: 创建 `backend/src/shared/models/risk_event.py`**

```python
from datetime import datetime
from sqlalchemy import String, DateTime, BigInteger, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode


class RiskEvent(Base, TimestampMixin):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # 例如: CIRCUIT_BREAKER_TRIGGERED, STOP_LOSS_HIT, API_ERROR, DAILY_LOSS_LIMIT
    symbol: Mapped[str | None] = mapped_column(String(20))
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    position_id: Mapped[int | None] = mapped_column(BigInteger)
```

- [ ] **Step 11: 创建 `backend/src/shared/models/experience.py`**

```python
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, BigInteger, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode


class ExperienceRecord(Base, TimestampMixin):
    """
    交易经验库（V0.1 基础版）：
    记录已平仓交易的结构化结果，不做 LLM 摘要。
    """
    __tablename__ = "experience_store"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    trade_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    regime: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    indicator_snapshot: Mapped[dict | None] = mapped_column(JSON)   # 开仓时指标快照
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    exit_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    exit_reason: Mapped[str] = mapped_column(String(30), nullable=False)
    holding_seconds: Mapped[int | None] = mapped_column(BigInteger)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

- [ ] **Step 12: 创建 `backend/src/shared/models/report.py`**

```python
from datetime import date
from sqlalchemy import String, Numeric, Date, BigInteger, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.models.base import Base, TimestampMixin
from src.shared.enums import TradingMode


class DailyReport(Base, TimestampMixin):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losing_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    win_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    total_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    total_pnl_pct: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0)
    max_single_loss: Mapped[float | None] = mapped_column(Numeric(20, 8))
    max_drawdown: Mapped[float | None] = mapped_column(Numeric(20, 8))
    risk_events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[dict | None] = mapped_column(JSON)  # 典型案例等补充信息
```

- [ ] **Step 13: 更新 `backend/src/shared/models/__init__.py`**

```python
from src.shared.models.base import Base
from src.shared.models.candle import Candle
from src.shared.models.account import AccountSnapshot
from src.shared.models.indicator import IndicatorSnapshot
from src.shared.models.regime import RegimeSnapshot
from src.shared.models.position import Position
from src.shared.models.decision import AIDecision
from src.shared.models.order import Order
from src.shared.models.trade import Trade
from src.shared.models.risk_event import RiskEvent
from src.shared.models.experience import ExperienceRecord
from src.shared.models.report import DailyReport

__all__ = [
    "Base",
    "Candle",
    "AccountSnapshot",
    "IndicatorSnapshot",
    "RegimeSnapshot",
    "Position",
    "AIDecision",
    "Order",
    "Trade",
    "RiskEvent",
    "ExperienceRecord",
    "DailyReport",
]
```

- [ ] **Step 14: 运行模型测试**

```bash
cd backend && source .venv/bin/activate
pytest tests/unit/test_models.py -v
```

Expected: 2 个测试 PASS

- [ ] **Step 15: 提交**

```bash
git add backend/src/shared/models/ backend/tests/unit/test_models.py
git commit -m "feat: add all SQLAlchemy database models"
```

---

### Task 8: Alembic 迁移配置和建表

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/scripts/init_db.py`
- Create: `backend/scripts/upgrade_db.py`
- Test: `backend/tests/integration/test_migrations.py`

- [ ] **Step 1: 创建 `backend/alembic.ini`**

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: 创建 `backend/migrations/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 3: 创建 `backend/migrations/env.py`**

```python
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 将 src/ 加入路径，确保模型可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shared.config import get_settings
from src.shared.models import Base  # 导入所有模型，确保 Base.metadata 包含全部表

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    settings = get_settings()
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = get_settings()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 创建 `backend/scripts/init_db.py`**

```python
"""初始化数据库：生成初始 Alembic 迁移并执行"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Generating initial migration...")
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "initial_schema"],
        check=True,
    )
    print("Running migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 创建 `backend/scripts/upgrade_db.py`**

```python
"""运行所有待执行的 Alembic 迁移"""
import subprocess
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Running pending migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Migrations complete.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 先写失败集成测试 `backend/tests/integration/test_migrations.py`**

```python
import pytest
from sqlalchemy import create_engine, inspect
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command
import os


@pytest.fixture(scope="module")
def migrated_db():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        # 运行所有迁移
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "../../alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(url)
        yield engine


def test_all_tables_created(migrated_db):
    inspector = inspect(migrated_db)
    tables = inspector.get_table_names()
    expected = [
        "candles", "account_snapshots", "indicator_snapshots",
        "regime_snapshots", "positions", "ai_decisions",
        "orders", "trades", "risk_events", "experience_store", "daily_reports",
    ]
    for table in expected:
        assert table in tables, f"Table '{table}' not found in DB"


def test_all_tables_have_trading_mode(migrated_db):
    """所有表均含 trading_mode 列"""
    inspector = inspect(migrated_db)
    tables_requiring_trading_mode = [
        "candles", "account_snapshots", "indicator_snapshots", "regime_snapshots",
        "positions", "ai_decisions", "orders", "trades",
        "risk_events", "experience_store", "daily_reports",
    ]
    for table in tables_requiring_trading_mode:
        cols = {c["name"] for c in inspector.get_columns(table)}
        assert "trading_mode" in cols, f"Table '{table}' missing trading_mode column"


def test_candles_unique_index(migrated_db):
    inspector = inspect(migrated_db)
    indexes = inspector.get_indexes("candles")
    index_names = [i["name"] for i in indexes]
    assert "ix_candles_symbol_timeframe_open_time" in index_names
```

- [ ] **Step 7: 生成初始迁移（需要 dev postgres 运行中）**

```bash
make dev-up   # 确保 postgres 运行
cd backend && source .venv/bin/activate
alembic revision --autogenerate -m "initial_schema"
```

Expected: `migrations/versions/xxxx_initial_schema.py` 文件生成，包含所有 11 张表。

- [ ] **Step 8: 运行迁移测试**

```bash
cd backend && source .venv/bin/activate
pytest tests/integration/test_migrations.py -v
```

Expected: 3 个测试 PASS

- [ ] **Step 9: 对本地 dev 数据库执行迁移**

```bash
make upgrade-db
```

Expected: `INFO [alembic] Running upgrade -> xxxx, initial_schema`

- [ ] **Step 10: 提交**

```bash
git add backend/alembic.ini backend/migrations/ backend/scripts/
git add backend/tests/integration/test_migrations.py
git commit -m "feat: add Alembic migrations for all database tables"
```

---

## Chunk 4: 完整验证与收尾

### Task 9: 运行全部测试 + lint

- [ ] **Step 1: 运行所有测试**

```bash
make test
```

Expected:
- `tests/unit/test_config.py` — 5 PASS
- `tests/unit/test_models.py` — 2 PASS
- `tests/api/test_health.py` — 2 PASS
- `tests/integration/test_db.py` — 2 PASS
- `tests/integration/test_migrations.py` — 3 PASS
- 总计：14 PASS，0 FAIL

- [ ] **Step 2: 运行 lint**

```bash
make lint
```

Expected: 无 linter 错误。

- [ ] **Step 3: 验证 Docker Compose 完整启动**

```bash
make dev-up
make dev-backend &  # 后台运行
sleep 3
curl http://localhost:8000/health
```

Expected: `{"status":"ok","trading_mode":"testnet","version":"0.1.0"}`

- [ ] **Step 4: 最终提交**

```bash
# 注意：明确指定文件，不使用 git add -A（避免意外包含 .env 敏感文件）
git add backend/src/ backend/tests/ backend/migrations/ backend/scripts/
git add backend/pyproject.toml backend/alembic.ini
git add docker/ Makefile .env.example .gitignore
git commit -m "feat: complete Plan 1 - project foundation ready"
```

---

## 完成标准

Plan 1 完成后，项目应满足：

- [ ] `make dev-up` 可启动 postgres 和 redis
- [ ] `make dev-backend` 可启动 FastAPI，`/health` 返回 200
- [ ] `make upgrade-db` 可创建所有 11 张数据库表
- [ ] `make test` 14 个测试全部通过
- [ ] `make lint` 无报错
- [ ] 所有代码已提交到 git

**下一步：Plan 2 — 数据层（Binance 接入 + 技术指标 + Regime 识别）**
