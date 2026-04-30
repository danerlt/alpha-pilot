# AlphaPilot 后端按 FastAPI 项目模板 v3 全量重构 — 设计文档

- **状态**: 待审阅
- **日期**: 2026-04-30
- **作者**: Claude（与老板协作 brainstorming 产出）
- **关联文档**:
  - 模板原文：`docs/fastapi-project-template-v3.md`
  - 项目记忆：`.claude/memory/MEMORY.md`、`CLAUDE.md`

---

## 1. 背景与目标

### 1.1 现状

AlphaPilot 是面向 Binance 的 AI 自主数字货币现货交易系统，已实现 Phase 1/2 + Phase 3 收尾。当前后端结构：

- 单 FastAPI 进程，APScheduler 内嵌在 `lifespan`（策略循环 15min、持仓监控 10s）
- 业务按 DDD 风格组织（`src/{execution,insight,strategy,events,control,services,workers,...}/`）
- DB session 通过 `src/shared/db.py` 提供（同步 SQLAlchemy）
- 配置集中在 `src/configs/app_configs.py` 单类，包含交易参数 / Binance / LLM / 安全密钥等
- 响应通过 FastAPI 默认机制（Pydantic model + `HTTPException`）
- 测试 53 通过

### 1.2 重构目标

参照 `fastapi-project-template-v3.md` 提供的工程规范，全量重构后端结构，使其继承模板的：

- 严格四层分层（Controller → Service → CRUD → Model）+ BaseCrud 父类模式
- 多继承聚合配置体系（按功能域拆类）
- 统一响应（`Response[T]`）+ 统一异常树 + 全局 exception handler
- 标准中间件栈（CorrelationId / RequestLogging / ErrorLogging）
- 进程拆分（`web` + `scheduler` 两进程独立守护）
- 工程化基础设施（`src/db/` 集中、`src/utils/` 标准工具）

同时**保持 alpha-pilot 业务侧零行为变化**：决策、风控、执行、监控的业务规则不在本次重构范围内。

### 1.3 与模板的差异（PostgreSQL 适配 + 项目特化裁剪）

模板针对 MySQL + funboost，alpha-pilot 是 PostgreSQL + 单 Pod 部署，本次重构对模板做如下裁剪：

| 模板原项 | 本次方案 | 原因 |
|---------|----------|------|
| MySQL 8.0 + `pymysql`/`mysqlclient` | PostgreSQL 16 + `psycopg2-binary` | 项目既定技术栈 |
| `sql_mode='STRICT_TRANS_TABLES'` listener | 无 | PG 默认严格 |
| funboost 异步任务 + Redis Stream broker | APScheduler + PostgreSQL JobStore + Redis 锁 | 单 Pod 单实例场景，funboost 是过度工程 |
| `web` + `worker` + `scheduler` 三进程 | `web` + `scheduler` 双进程 | 不引入 funboost 后 worker 无独立存在意义 |
| `nb_log` 日志库 | Python stdlib `logging`（保留现有体系） | 减少依赖，当前体系已稳定 |
| `msgspec` JSON 加速 | stdlib JSON | alpha-pilot 不是高吞吐 Web，收益小 |
| Phoenix LLM 追踪 | 不引入 | YAGNI |
| 飞书 SDK / 飞书 WS leader | 不引入 | 项目无相关业务 |
| supervisor 单镜像多进程 | Docker Compose 多 service（web service + scheduler service） | 与现有部署形态一致 |
| 目录全扁平按层（`services/<entity>_service.py` 一实体一文件） | **B-Hybrid**：DB 层扁平 + 业务层按领域聚合 | alpha-pilot 业务流程跨领域强耦合，扁平按层会让跨实体编排失序（详见 §3.1） |

### 1.4 约束与不变量

- **同步 SQLAlchemy 全栈**：HTTP / scheduler / CRUD 全部同步，禁止 AsyncSession（与模板一致）
- **单 Pod 部署**：所有方案以单 Pod 为基准，多 Pod 仅为高可用，不为并行扩容
- **业务行为零变化**：所有业务规则（决策兜底、风控熔断、幂等 trace_id、CHAOTIC 降级）保持当前行为
- **数据库 schema 允许重建**：本次重构允许删除现有 `migrations/versions/*` 重新生成（id 字段从 `String(32) UUID` 升级到 `BigInteger autoincrement`），所有 schema 变更走 `alembic revision`（CLAUDE.md 强制）；当前项目处于 dev/test 阶段（无生产数据），重建数据库可接受
- **CLAUDE.md 工作流强制**：每阶段交付 = 编译通过 + 测试全绿 + commit + push + dev 部署验证 + worklog

---

## 2. 关键技术决策汇总

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 进程模型 | `api` + `scheduler` 双 service | scheduler 与 HTTP 故障隔离，scheduler 失败不影响用户接口 |
| api 进程并发 | uvicorn 多 worker（`UVICORN_WORKER_NUM` ≥ 1，按 CPU 核数配） | scheduler 已独立，api 进程内无单例追踪器，可放开多 worker |
| scheduler 部署 | **单容器**（不引入多 Pod 选主） | alpha-pilot 是单 Pod 部署，单容器最简 |
| Session 模型 | 同步 SQLAlchemy `Session` | 与模板一致；交易系统优先正确性而非 I/O 并发 |
| 异步任务框架 | APScheduler，**不引入 funboost** | 单 Pod 场景下 funboost 是过度工程 |
| Job 元数据持久化 | `SQLAlchemyJobStore`（PostgreSQL `apscheduler_jobs` 表） | 重启不丢 job 状态；与业务库一致便于备份 |
| 主键设计 | 每个 model 自定义 `id: Mapped[int]` + `BigInteger` + `autoincrement=True`，**不放在 Base** | 与模板差异化；自增主键便于按时间排序、索引效率好 |
| `trading_mode` 字段归属 | 通过 `TradingModeMixin` 显式继承（不在 Base） | 不是所有表都需要环境隔离（如 User）；显式胜过隐式 |
| 目录布局 | **B-Hybrid**：DB 层扁平 + 业务层按领域聚合 | 见 §3.1 |
| 响应体系 | `Response[T]` 包装 + `@api_response` + 全局 exception handler | 业务异常统一 HTTP 200 + body `success: false`；HTTP 状态码留给传输层语义 |
| 异常树 | 严格按模板：`AppBaseException` → `ServiceException` / `DBException` / `ParamsException` / `RedisException` + 业务专属子类 | 业务代码统一抛 `ServiceException`；CRUD 层抛 `DBException` |
| 配置体系 | `pydantic-settings` 多继承（8 个子配置类） | 按功能域分类，便于增删 |
| 中间件 | CorrelationId（最外层）+ RequestLogging + ErrorLogging | 与模板一致 |
| 推进策略 | 五阶段推进（详见 §6） | 增量式，每阶段独立可部署可回滚 |

---

## 3. 终态架构

### 3.1 目录布局（B-Hybrid）

**核心原则**：DB 层（`models/` `schemas/` `cruds/`）全局扁平 ↔ 业务层（`services/` `controllers/`）按业务领域聚合。

```
backend/
├── pyproject.toml                          # 依赖按职责分组（ruff 配置 / mypy 配置统一）
├── uv.lock
├── .python-version                         # 3.12
│                                            # 注：原 backend/alembic.ini 删除，迁到 src/db/alembic.ini
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.scheduler
│   └── entrypoint.sh
├── scripts/
│   ├── start_api.py                        # FastAPI 进程入口（多 worker）
│   ├── start_scheduler.py                  # APScheduler 进程入口（单容器）
│   ├── init_db.py                          # CREATE DATABASE + 连通性 ping
│   └── upgrade_db.py                       # alembic upgrade head + Redis 分布式锁（多 Pod 安全）
└── src/
    ├── app.py                              # FastAPI 应用工厂（替代 src/app/app.py）
    │
    ├── configs/
    │   ├── __init__.py                     # 暴露 configs 单例
    │   └── app_configs.py                  # 8 个子配置多继承
    │
    ├── common/
    │   ├── constants.py                    # 路径 / 业务常量
    │   ├── enums.py                        # 全局 Enum 集合
    │   ├── pagination.py                   # 通用分页入参 / 出参
    │   ├── schema.py                       # 通用 Pydantic 类型基类
    │   ├── api_response.py                 # @api_response 装饰器
    │   ├── response/
    │   │   ├── response_schema.py          # Response[T] / ResponseBase
    │   │   └── response_code.py            # 业务码常量
    │   └── exception/
    │       ├── errors.py                   # BizError 树
    │       └── exception_handler.py        # 全局 handler 注册
    │
    ├── controllers/
    │   ├── router.py                       # app_router = system + api/v1
    │   ├── api/v1/
    │   │   ├── router.py                   # v1 子路由聚合
    │   │   ├── execution/
    │   │   │   ├── positions.py
    │   │   │   ├── orders.py
    │   │   │   ├── trades.py
    │   │   │   └── account.py
    │   │   ├── strategy/
    │   │   │   └── decisions.py
    │   │   ├── risk/
    │   │   │   ├── events.py
    │   │   │   └── kill_switch.py
    │   │   ├── reports.py
    │   │   ├── auth.py
    │   │   ├── runtime_config.py
    │   │   ├── commands.py
    │   │   └── events_catchup.py
    │   └── system/
    │       ├── router.py
    │       └── health.py
    │
    ├── services/                           # 业务编排层（按领域聚合）
    │   ├── execution/
    │   │   ├── order_execution.py
    │   │   ├── execution_guard.py
    │   │   ├── monitoring.py
    │   │   ├── account_state.py
    │   │   └── market_data.py
    │   ├── insight/
    │   │   ├── indicators.py
    │   │   ├── regime.py
    │   │   └── experience.py
    │   ├── strategy/
    │   │   ├── decision_engine.py
    │   │   ├── proposal.py
    │   │   └── pipeline.py                 # 跨领域编排：完整策略循环
    │   ├── risk/
    │   │   ├── kill_switch.py
    │   │   └── risk_events.py
    │   ├── reporting.py
    │   ├── auth.py
    │   ├── manual_ops.py
    │   ├── event_bus.py                    # outbox / inbox 编排
    │   └── admin_bootstrap.py
    │
    ├── cruds/                              # 数据访问层（全局扁平）
    │   ├── base_crud.py                    # BaseCrud[ModelT]
    │   ├── position_crud.py
    │   ├── order_crud.py
    │   ├── trade_crud.py
    │   ├── decision_crud.py
    │   ├── risk_event_crud.py
    │   ├── account_snapshot_crud.py
    │   ├── kline_crud.py
    │   ├── indicator_crud.py
    │   ├── regime_crud.py
    │   ├── experience_crud.py
    │   ├── report_crud.py
    │   ├── kill_switch_crud.py
    │   ├── manual_op_crud.py
    │   ├── outbox_crud.py
    │   ├── inbox_crud.py
    │   ├── user_crud.py
    │   └── system_settings_crud.py
    │
    ├── models/                             # SQLAlchemy ORM（全局扁平）
    │   ├── __init__.py                     # 显式导入 + __all__
    │   ├── base.py                         # DeclarativeBase + 公共字段
    │   ├── enums.py                        # ORM 枚举
    │   ├── position.py
    │   ├── order.py
    │   ├── trade.py
    │   ├── decision.py
    │   └── ...                             # 共 ~17 个实体
    │
    ├── schemas/                            # Pydantic 入参 / 出参（全局扁平）
    │   ├── pagination.py
    │   ├── auth.py
    │   ├── position.py
    │   ├── order.py
    │   └── ...                             # 一模块一文件
    │
    ├── core/                               # 业务核心：无状态计算 + 外部客户端
    │   ├── exchange/
    │   │   └── binance_client.py           # python-binance 封装（mainnet/testnet 切换）
    │   ├── llm/
    │   │   ├── client.py                   # OpenAI 兼容客户端（DeepSeek 默认）
    │   │   └── prompts/                    # Prompt 模板
    │   ├── indicators/
    │   │   └── calculators.py              # pandas-ta 封装（EMA/RSI/MACD/ATR/BB）
    │   └── trace.py                        # 幂等 trace_id 生成（SHA256 ...）
    │
    ├── db/
    │   ├── alembic.ini                     # 迁移配置（迁入此处）
    │   ├── engines.py                      # PostgreSQL 同步 engine + SessionLocal
    │   ├── session.py                      # get_db / get_db_session / CurrentSession
    │   ├── migrate.py                      # 迁移入口（被 upgrade_db.py 调用）
    │   └── migrations/
    │       ├── env.py
    │       └── versions/                   # 现有 migration 平移
    │
    ├── middleware/
    │   ├── request_logging_middleware.py
    │   └── error_logging_middleware.py
    │
    ├── schedulers/
    │   ├── __init__.py
    │   ├── strategy_pipeline_scanner.py    # 调用 services/strategy/pipeline.py
    │   ├── position_monitor_scanner.py     # 调用 services/execution/monitoring.py
    │   └── event_shuttle.py                # outbox → Redis Pub/Sub 推送 daemon（详见 §4.8.2）
    │
    └── utils/
        ├── log.py                          # init_logger / get_logger
        ├── redis.py                        # redis_client + 锁工具
        ├── time.py                         # 北京时间工具
        ├── uuid.py
        ├── request_id.py                # HTTP 链路 X-Request-ID 读取工具（不是业务幂等 trace_id）
        ├── json.py                         # 自定义 JSON 编解码（datetime/Enum/Decimal）
        └── serializers.py                  # FastAPI 响应类（如有特殊定制）
```

### 3.2 进程模型

```
┌──────────────────────────────────────────────────────────────────┐
│                       Docker Compose                              │
├──────────────────────────────┬───────────────────────────────────┤
│   api service                │   scheduler service                │
│   (可水平扩，多 worker)      │   (单容器，独占)                   │
│   ----------------           │   ----------------                 │
│   入口: scripts/start_api.py │   入口: scripts/start_scheduler.py │
│                              │                                    │
│   职责:                       │   职责:                            │
│   - FastAPI HTTP 服务         │   - APScheduler 调度策略循环/监控  │
│   - WebSocket /ws            │   - SQLAlchemyJobStore (PG)        │
│   - Redis Pub/Sub 订阅广播   │   - APScheduler 后台线程 + 主线程 │
│                              │     BRPOP 消费任务队列            │
│   - lifespan 不启动 scheduler│   - 业务直接执行（不分发到 worker）│
│                              │                                    │
│   uvicorn workers=N (按 CPU) │   单实例运行（无 leader 选举）     │
└──────────────────────────────┴───────────────────────────────────┘
                  ↓                              ↓
              ┌──────────────────────────────────────┐
              │  PostgreSQL 16  +  Redis 7           │
              │  - 业务库 + apscheduler_jobs 表      │
              │  - Pub/Sub                            │
              └──────────────────────────────────────┘
```

**关键约束**：
- `api` 进程 `uvicorn workers=N`（N 由 `UVICORN_WORKER_NUM` 配置，默认按 CPU 核数）；不引入 funboost 后 api 进程内无进程级单例（追踪器、调度器都不在），可放开多 worker
- `api` 进程 `lifespan` 内**不再启动 APScheduler**（由 scheduler 进程独占）
- `scheduler` 进程**不引用 FastAPI**，直接通过 `get_db_session()` 调用 service 层
- `scheduler` 部署为**单容器**（docker-compose `replicas: 1`）；不需要多 Pod 选主、无需 leader 锁
- API 多 worker 与 WebSocket 兼容性：每个 worker 各自维护一个 Redis Pub/Sub 订阅者，每个 WebSocket 连接绑定到接收它的 worker；广播事件由每个 worker 推给本 worker 内的连接（无重复推送，无丢失）

---

## 4. 各层详细设计

### 4.1 配置层（`src/configs/app_configs.py`）

按功能域拆 8 个子配置类，`AppConfig` 多继承聚合。`pydantic-settings` 加载顺序：代码默认 → `.env` → 环境变量。

```python
# 子类清单
class ServiceConfig(BaseSettings):       # ENVIRONMENT / LOG_LEVEL / UVICORN_WORKER_NUM=1
class CORSConfig(BaseSettings):          # ENABLE_CORS / CORS_ALLOWED_ORIGINS / CORS_EXPOSE_HEADERS
class PostgreSQLConfig(BaseSettings):    # PG_USER / PG_PASSWORD / PG_HOST / PG_PORT / PG_DB / POOL_SIZE / POOL_MAX_OVERFLOW / DB_CONNECT_TIMEOUT
                                         # 提供 db_uri property: postgresql+psycopg2://...
class RedisConfig(BaseSettings):         # REDIS_HOST / REDIS_PORT / REDIS_DB / REDIS_PASSWORD / REDIS_KEY_PREFIX
                                         # 提供 redis_url property
class SchedulerConfig(BaseSettings):     # STRATEGY_LOOP_INTERVAL_MINUTES (default 15)
                                         # POSITION_MONITOR_INTERVAL_SECONDS (default 10)
                                         # APSCHEDULER_JOBS_TABLE (default "apscheduler_jobs")
                                         # TASK_QUEUE_KEY (default "alphapilot:tasks")        — Redis List 异步任务队列
                                         # EVENT_BUS_CHANNEL (default "alphapilot:events")    — Redis Pub/Sub 频道
                                         # EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS (default 3)      — outbox 推送失败 max 后进死信
                                         # EVENT_SHUTTLE_BATCH_SIZE (default 50)              — 每轮取多少条 outbox
                                         # EVENT_SHUTTLE_IDLE_SLEEP_SECONDS (default 0.5)     — 无待发事件时休眠秒数
                                         # SCHEDULER_GRACEFUL_SHUTDOWN_SECONDS (default 60)   — 与 docker-compose stop_grace_period 一致
class ExchangeConfig(BaseSettings):      # TRADING_MODE / BINANCE_API_KEY / BINANCE_API_SECRET
class LLMConfig(BaseSettings):           # LLM_BASE_URL / LLM_API_KEY / LLM_MODEL / LLM_TIMEOUT_SECONDS
class RiskConfig(BaseSettings):          # MAX_POSITION_SIZE_PCT / MAX_DAILY_LOSS_PCT / MAX_CONSECUTIVE_LOSSES / MAX_SINGLE_RISK_PCT
class SecurityConfig(BaseSettings):      # APP_AUTH_SECRET_KEY / APP_CONFIG_MASTER_KEY / DEFAULT_ADMIN_*
                                         # 启动时 _validate_secrets 检测弱密钥（沿用现有逻辑）

class AppConfig(ServiceConfig, CORSConfig, PostgreSQLConfig, RedisConfig,
                SchedulerConfig, ExchangeConfig, LLMConfig, RiskConfig, SecurityConfig):
    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore")
```

`example.env` 字段顺序与 AppConfig 基类列表严格一致；环境变量黑名单规则（CLAUDE.md）保持不变。

### 4.2 DB 层（`src/db/`）

#### 4.2.1 `engines.py` — PostgreSQL 同步 engine

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.configs import configs

sync_engine = create_engine(
    configs.db_uri,                      # postgresql+psycopg2://user:pwd@host:port/db
    pool_size=configs.POOL_SIZE,
    max_overflow=configs.POOL_MAX_OVERFLOW,
    pool_pre_ping=True,                  # 防 PG 连接被 idle_in_transaction_session_timeout 杀掉
    pool_recycle=3600,
    connect_args={"connect_timeout": configs.DB_CONNECT_TIMEOUT},
    json_serializer=_dumps,              # 复用模板自定义 JSON 编码（datetime/Enum）
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,              # 与模板一致；commit 后 service 显式 refresh
)
```

**与模板差异**：
- 不需要 `sql_mode` listener（PG 默认严格模式）
- 不需要 `read_timeout` / `write_timeout`（psycopg2 不支持，PG 通过 `statement_timeout` 在 server 端控制；本期不引入）

#### 4.2.2 `session.py` — 双对外名字

```python
def get_db() -> Generator[Session, None, None]:
    """通用 session 工厂；不自动 commit；异常 rollback。"""
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()

get_db_session = contextlib.contextmanager(get_db)            # 给 scheduler / 脚本 with 语句用
CurrentSession: TypeAlias = Annotated[Session, Depends(get_db)]  # 给 FastAPI router 用
```

#### 4.2.3 `models/base.py` — 公共字段基类 + Mixin

`Base` **不包含 `id` 字段**（与模板差异化设计）；id 由每个 model 单独定义。Base 只放**所有表都需要**的字段；与"交易环境隔离"相关的 `trading_mode` 通过 **Mixin 显式选择性继承**，按需加入。

```python
class Base(DeclarativeBase):
    """所有表的公共字段：软删 + 时间戳"""
    enable_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("TRUE"))
    delete_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=TimeUtils.now, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=TimeUtils.now, onupdate=TimeUtils.now)


class TradingModeMixin:
    """需要按 testnet/mainnet 隔离数据的表显式继承"""
    trading_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="testnet/mainnet 数据隔离"
    )
```

**`trading_mode` 字段归属规则**：

| 需要 `trading_mode` 的 model（继承 `Base, TradingModeMixin`） | 不需要的 model（仅继承 `Base`） |
|---|---|
| Position / Order / Trade（交易实体，环境严格隔离） | User（账号体系不绑定交易环境，登录后选环境） |
| Decision / RiskEvent（决策与风控按环境） | SystemSettings（系统级配置，如需按环境隔离则在 key 里编码） |
| AccountSnapshot（账户余额按环境） | （Alembic 自管的 `apscheduler_jobs` 不在 SQLAlchemy metadata 里） |
| KlineData / Indicator / Regime（行情按环境，因 testnet 与 mainnet 行情源不同） | |
| ExperienceRecord / Report（基于交易实体派生） | |
| KillSwitch（按环境停机，testnet 停机不应影响 mainnet 反之亦然） | |
| ManualOp / Outbox / Inbox / TaskRequest（业务事件，跟随主业务） | |

**示例**：

```python
# src/models/position.py（需要 trading_mode）
class Position(Base, TradingModeMixin):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # ... 业务字段


# src/models/user.py（不需要 trading_mode）
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    # ... 业务字段
```

**复合索引建议**（仅 `TradingModeMixin` 表）：业务高频查询模式是「按 trading_mode + 业务字段过滤」，对应 model 应该建 `(trading_mode, symbol)` / `(trading_mode, status)` 等复合索引。

#### 4.2.4 主键改造的全局影响

- **每个 model 文件第一字段必须是 `id`**：`Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)`
- **跨表关联列同步改 `BigInteger`**：`Order.position_id`、`Position.decision_id`、`Trade.decision_id`、`RiskEvent.decision_id`、`Trade.position_id` 等。CLAUDE.md 强制"不允许外键约束"，仅 `index=True` 加速 join
- **`get_uuid_without_hyphen` 默认生成器不再用作主键**（utils 函数可保留供 trace_id 之类业务键用）
- **业务幂等键保持原样**：`Order.trace_id = SHA256(decision_id:symbol:action)` 仍是 `String(64)`，业务键不是主键
- **`migrations/versions/*` 全量删除**，按新 schema 重新 `alembic revision --autogenerate -m "init schema with bigint pk"` 生成单个初始 migration

### 4.3 CRUD 层（`src/cruds/base_crud.py`）

`BaseCrud[ModelT]` 提供 95% 标准 CRUD：

```python
class BaseCrud(Generic[ModelT]):
    model: type[ModelT]

    def add(self, session: Session, **kwargs) -> ModelT: ...
    def get(self, session: Session, id: str) -> ModelT:                 # 不存在抛 NotFoundError
    def get_or_none(self, session: Session, id: str) -> ModelT | None:  # 不存在返 None
    def list(self, session: Session, *, filters: dict, order_by, page, page_size) -> Page[ModelT]: ...
    def update(self, session: Session, id: str, **kwargs) -> ModelT: ...
    def delete(self, session: Session, id: str) -> None:                # 软删（delete_flag=True）
    def hard_delete(self, session: Session, id: str) -> None: ...

class PositionCrud(BaseCrud[Position]):
    model = Position

    # 实体专属方法
    def get_open_positions(self, session: Session, symbol: str | None = None) -> list[Position]: ...
    def find_by_decision_id(self, session: Session, decision_id: str) -> Position | None: ...

position_crud = PositionCrud()  # 单例
```

**强制规范**：
- service 层只调 `xxx_crud.method()`，不写裸 SQL / `session.query(Model)`
- crud 方法**不 commit**；commit 由 service 显式调用
- 命名规范：
  - `get_xxx`（不存在抛 `DBException(NOT_FOUND)`）
  - `get_xxx_or_none`（不存在返 None）
  - `find_xxx` / `find_by_xxx`（按条件查询，返列表，不存在返空列表）
  - `add` / `bulk_add` / `update` / `delete`（CRUD 基本操作）
  - **状态变更动词**：`mark_<status>`（如 `mark_running` / `mark_done` / `mark_failed` / `mark_published` / `mark_dead_letter`），用于明确语义的状态机迁移
  - **批量状态变更**：`bulk_mark_<status>` 接 `status_in=[...]` 参数
  - **重试 / 失败次数累加**：`bump_failed_attempts(id, error: str)`
  - **进度更新**：`update_progress(id, progress: int)`

### 4.4 Service 层（`src/services/{domain}/`）

按 §3.1 的领域聚合组织。Service 类 + 单例模式。

```python
class OrderExecutionService:
    def execute_decision(self, session: Session, decision: Decision) -> Order:
        # 1. 通过 cruds 读数据
        position = position_crud.get_by_symbol(session, decision.symbol)
        # 2. 调用 core/ 无状态计算
        trace_id = generate_trace_id(decision.id, decision.symbol, decision.action)
        # 3. 通过 cruds 写数据
        order = order_crud.add(session, trace_id=trace_id, ...)
        session.commit()
        session.refresh(order)
        # 4. 写 outbox（事件总线）
        event_bus_service.publish(session, OrderCreatedEvent(...))
        return order

order_execution_service = OrderExecutionService()
```

**跨领域编排**：放在领域语义最强的 service 里（如完整策略循环放 `services/strategy/pipeline.py`，因为这是策略域的"主流程"）。

**事件总线接口约定**（`src/services/event_bus.py`）：

```python
# src/common/events.py — 所有事件的基类
class BaseEvent(BaseModel):
    user_id: int | None = None
    request_id: str | None = None              # HTTP 链路 ID（如有）
    occurred_at: datetime = Field(default_factory=TimeUtils.now)

# 业务事件示例
class StrategyDecisionEvent(BaseEvent):
    decision_id: int
    symbol: str
    action: str

class OrderCreatedEvent(BaseEvent):
    order_id: int
    decision_id: int
    symbol: str

class TaskStateChangedEvent(BaseEvent):
    task_id: int
    status: str                                # running/done/failed
    result: dict | None = None
    error: str | None = None

class TaskProgressEvent(BaseEvent):
    task_id: int
    progress: int                              # 0-100
    current_item: dict | None = None


# src/services/event_bus.py
class EventBusService:
    def publish(self, session: Session, event: BaseEvent) -> None:
        """写 outbox 表（持久化）。后续由 EventShuttle worker 异步推送到
        Redis Pub/Sub（确保不丢消息），api 进程的 redis_to_ws_broadcaster 协程
        消费 Redis Pub/Sub 转发给 WebSocket 客户端。

        约定：本方法**不 commit**，commit 由调用方（service 编排层）控制；
              这样事件落库与业务数据写入处于同一事务，保证原子性。
        """
        outbox_crud.add(
            session,
            event_type=type(event).__name__,
            payload=event.model_dump(mode="json"),
            user_id=event.user_id,
            status="pending",
        )

event_bus_service = EventBusService()
```

**事件流向链路**：
```
Service 层
  ↓ event_bus_service.publish(session, event)  [写 outbox 表]
  ↓ session.commit()                            [业务数据 + outbox 同事务提交]

EventShuttle worker（独立 daemon thread / scheduler job）
  ↓ 扫描 outbox.status=pending
  ↓ 推送到 Redis Pub/Sub channel "alphapilot:events"
  ↓ 标记 outbox.status=published

api 进程（每个 worker 各一个协程）
  ↓ redis_to_ws_broadcaster 订阅 Redis channel
  ↓ 按 event.user_id 路由到对应 WebSocket 连接
  ↓ ws.send_json(event)
```

### 4.5 Controller 层（`src/controllers/api/v1/{domain}/`）

```python
# src/controllers/api/v1/execution/positions.py
from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.db.session import CurrentSession
from src.schemas.position import PositionRead
from src.services.execution.order_execution import order_execution_service

router = APIRouter(prefix="/positions", tags=["execution.positions"])

@router.get("/{position_id}", response_model=Response[PositionRead])
@api_response()
def get_position(position_id: str, session: CurrentSession) -> PositionRead:
    position = position_crud.get(session, position_id)   # 不存在自动抛 NotFoundError
    return PositionRead.model_validate(position)

@router.post("/{position_id}/close", response_model=Response[PositionRead])
@api_response()
def close_position(position_id: str, session: CurrentSession) -> PositionRead:
    position = order_execution_service.close_position_manually(session, position_id)
    return PositionRead.model_validate(position)
```

**规范**：
- controller 只做参数校验 + service 调用 + DTO 转换；**禁止写业务逻辑**
- 所有 controller 函数加 `@api_response()` 装饰器；返回值就是 `data` 字段内容
- 业务异常通过抛 `ServiceException` 等 `AppBaseException` 子类传递；`HTTPException` 不再用于业务错误

**Schema 命名规范（强制）**：

| 用途 | 后缀 | 示例 |
|------|------|------|
| 实体响应（GET 返回 / List 元素） | `xxxRead` | `PositionRead`, `OrderRead`, `DecisionRead` |
| 创建入参（POST body） | `xxxCreate` | `OrderCreate`, `LoginCreate` |
| 更新入参（PATCH/PUT body） | `xxxUpdate` | `OrderUpdate`, `RuntimeConfigUpdate` |
| 非实体的操作结果 / 复合返回 | `xxxOut` | `LoginOut`（access_token 包）、`TaskSubmitOut`、`CloseAllSubmitOut` |
| 复杂查询参数（多字段过滤） | `xxxQuery` | `OrderListQuery`, `TradeFilterQuery` |
| 分页响应 | `Paginated[xxxRead]` | `Paginated[OrderRead]` |
| service 之间传递的内部 dataclass | 业务名（无后缀） | `DecisionContext`, `GuardCheckResult`（放 `src/common/dataclasses.py`） |

**禁止使用的命名后缀**：`xxxVO`（Java 风）、`xxxDTO`（Java 风）、`xxxRes`（缩写违反 PEP 20）、`xxxResponse`（与外层 `Response[T]` envelope 撞名）、`xxxSchema`（过于宽泛）。

**`Paginated[T]` 泛型分页响应**（`src/common/schemas/pagination.py`）：

```python
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class Paginated(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(0, description="总条数")
    page_index: int = Field(1, description="当前页码（1-based）")
    page_size: int = Field(20, description="每页大小")
    pages: int = Field(0, description="总页数 = ceil(total / page_size)")
```

使用：`@router.get("", response_model=Response[Paginated[OrderRead]])`。

**字段语义（强制）**：
- `items` —— 当前页的数据列表
- `total` —— 总条数
- `page_index` —— 当前页码（1-based，第一页 = 1）
- `page_size` —— 每页大小
- `pages` —— 总页数（向上取整）

入参方向（`xxxQuery` 类）也用 `page_index` / `page_size` 命名，保持读写对称。

### 4.6 响应/异常体系（严格按模板 §8）

整体设计原则（与模板一致）：
- **业务异常统一返回 HTTP 200**，body 里 `success: false` + `code` + `message` 区分；只有真正的传输 / 网络错误（路径不存在、未授权等）才返回非 200
- **HTTP 状态码 = 传输层语义**；**业务 code = 业务层语义**；两者职责分离不互相侵入
- **业务代码禁止就地 `class XxxError(Exception)`**；如需新增异常子类，统一定义在 `src/common/exception/errors.py`

#### 4.6.1 `Response[T]` 结构

```python
# src/common/response/response_schema.py
class Response(BaseModel, Generic[T]):
    success: bool = Field(True)
    code: str = Field(ErrorCode.SUCCESS.code)        # 注意 code 是字符串（如 "0" / "400005"）
    message: str = Field(ErrorCode.SUCCESS.msg)
    detailMessage: str | None = Field(None)          # dev 环境回显完整 detail；prod 留空
    data: T | None = Field(None)


class ResponseBase:
    @staticmethod
    def success(data: Any = None) -> Response: ...
    @staticmethod
    def fail(code: str, message: str, detail: str | None = None) -> Response: ...

response_base = ResponseBase()
```

#### 4.6.2 `ErrorCode` 错误码枚举

```python
# src/common/response/response_code.py
class ErrorCode(Enum):
    SUCCESS = ("0", "成功")

    # 客户端错误 4xxxxx
    PARAM_ERROR       = ("400001", "参数错误")
    VALIDATION_ERROR  = ("400002", "参数校验失败")
    AUTH_ERROR        = ("400003", "认证失败")
    FORBIDDEN         = ("400004", "权限不足")
    NOT_FOUND         = ("400005", "资源不存在")
    RATE_LIMIT        = ("400006", "请求过于频繁")
    CONFLICT          = ("400009", "资源冲突")

    # 服务端错误 5xxxxx
    SYS_ERROR     = ("500001", "系统错误")
    SERVICE_ERROR = ("500002", "服务层错误")
    DB_ERROR      = ("500003", "数据库错误")
    REDIS_ERROR   = ("500006", "Redis 错误")

    # alpha-pilot 业务码 6xxxxx（业务专属）
    KILL_SWITCH_PAUSED      = ("600001", "系统紧急停机中")
    RISK_REJECTED           = ("600002", "风控校验未通过")
    IDEMPOTENCY_CONFLICT    = ("600003", "幂等键冲突")
    INSUFFICIENT_BALANCE    = ("600004", "账户余额不足")
    EXCHANGE_API_ERROR      = ("600005", "交易所接口异常")
    LLM_RESPONSE_INVALID    = ("600006", "LLM 响应格式异常")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def msg(self) -> str:
        return self.value[1]
```

#### 4.6.3 异常树（`src/common/exception/errors.py`）— 抛出时自动记 ERROR 日志

**核心特性**：所有 `AppBaseException` 子类抛出时**自动以 ERROR 级别记日志**，并通过 `type(self).__name__` 自动识别真实子类。日志同时输出 `extra={"exc_class", "exc_code"}` 用于结构化检索 / 告警过滤。

```python
import logging
import sys
import traceback as tb_mod
from typing import ClassVar

logger = logging.getLogger("app.exception")


class AppBaseException(Exception):
    """所有自定义异常的根基类。抛出时自动记 ERROR 日志，含文件名 + 行号 + 调用栈。"""

    auto_log: ClassVar[bool] = True            # 是否自动记日志
    auto_log_stack: ClassVar[bool] = True      # 是否带调用栈（高频/客户端类异常可关闭）

    def __init__(self, error_code: ErrorCode = ErrorCode.SYS_ERROR, message: str = "") -> None:
        self.error_code = error_code
        self.code = error_code.code
        self.message = message or error_code.msg
        super().__init__(self.message)
        if self.auto_log:
            self._auto_log()

    def _auto_log(self) -> None:
        """统一 ERROR 级；显式提取真实 raise 行的文件名 + 行号 + request_id + 调用栈。

        - sys._getframe(2) 取栈帧：0=_auto_log, 1=__init__, 2=raise 该异常的业务代码行
        - request_id 从 asgi-correlation-id（HTTP 链路）/ contextvars（scheduler 链路）读取，无则 "-"
          注意：这里的 request_id 指 HTTP 请求追踪 ID（X-Request-ID），与业务幂等 trace_id（如 Order.trace_id）不同
        - traceback.format_stack() 抓当前调用栈（call stack 等价于 raise 时即将传播的 traceback）
        - 本方法是该异常的**唯一日志记录点** —— 全局 handler 不再重复记录
        """
        frame = sys._getframe(2)
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        funcname = frame.f_code.co_name

        from src.utils.request_id import get_request_id   # 延迟 import 避免循环依赖
        request_id = get_request_id() or "-"

        # 抓调用栈（去掉 _auto_log + __init__ 两帧）
        stack_str = ""
        if self.auto_log_stack:
            stack_str = "".join(tb_mod.format_stack()[:-2])

        log_fmt = "[%s] code=%s msg=%s at %s:%d in %s() request_id=%s"
        log_args: list = [type(self).__name__, self.code, self.message,
                          filename, lineno, funcname, request_id]
        if stack_str:
            log_fmt += "\nCall stack:\n%s"
            log_args.append(stack_str)

        logger.error(
            log_fmt, *log_args,
            stacklevel=3,
            extra={
                "exc_class": type(self).__name__,
                "exc_code": self.code,
                "exc_file": filename,
                "exc_lineno": lineno,
                "exc_func": funcname,
                "request_id": request_id,
            },
        )


# ── 框架级异常 ──────────────────────────────────────────────────────────
class ServiceException(AppBaseException):
    def __init__(self, message: str = "", error_code: ErrorCode = ErrorCode.SERVICE_ERROR) -> None:
        super().__init__(error_code=error_code, message=message)


class DBException(AppBaseException):
    def __init__(self, message: str = "", error_code: ErrorCode = ErrorCode.DB_ERROR) -> None:
        super().__init__(error_code=error_code, message=message)


class ParamsException(AppBaseException):
    auto_log_stack = False                # 客户端参数错误，stack 无价值，关掉避免日志膨胀

    def __init__(self, message: str = "") -> None:
        super().__init__(error_code=ErrorCode.PARAM_ERROR, message=message)


class RedisException(AppBaseException):
    def __init__(self, message: str = "") -> None:
        super().__init__(error_code=ErrorCode.REDIS_ERROR, message=message)


# ── alpha-pilot 业务专属（统一在 errors.py 定义；禁止业务代码就地新增）─────
class KillSwitchPausedException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.KILL_SWITCH_PAUSED)

class RiskRejectedException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.RISK_REJECTED)

class IdempotencyConflictException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.IDEMPOTENCY_CONFLICT)

class InsufficientBalanceException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.INSUFFICIENT_BALANCE)

class ExchangeApiException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.EXCHANGE_API_ERROR)

class LLMResponseInvalidException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.LLM_RESPONSE_INVALID)
```

**自动记日志的行为**：

```python
# 业务代码（src/services/execution/execution_guard.py:87）
raise RiskRejectedException("日内亏损达 3.2% > 3%")

# 日志输出（一条记录，含定位 + 调用栈）：
2026-04-30 10:23:45 ERROR [RiskRejectedException] code=600002 msg=日内亏损达 3.2% > 3% \
  at /app/src/services/execution/execution_guard.py:87 in check_daily_loss() request_id=550e8400e29b41d4a716446655440000
Call stack:
  File "/app/scripts/start_api.py", line 5, in <module>
    main()
  File "/app/src/controllers/api/v1/execution/positions.py", line 45, in close_all
    result = order_execution_service.close_all(session, user_id)
  File "/app/src/services/execution/order_execution.py", line 78, in close_all
    execution_guard_service.check_daily_loss(session)
  File "/app/src/services/execution/execution_guard.py", line 87, in check_daily_loss
    raise RiskRejectedException(f"日内亏损达 {pct}% > {limit}%")

# extra 结构化字段（供日志聚合 / 告警过滤用）：
#   {"exc_class": "RiskRejectedException", "exc_code": "600002",
#    "exc_file": "/app/src/services/execution/execution_guard.py", "exc_lineno": 87,
#    "exc_func": "check_daily_loss", "request_id": "550e8400e29b41d4a716446655440000"}
```

**Stack 控制**（按异常子类配置）：

| 子类 | `auto_log_stack` | 说明 |
|------|----------------|------|
| `AppBaseException`（默认） | `True` | 业务异常都带 stack，便于追溯调用链 |
| `ServiceException` / `DBException` / `RedisException` 及其子类 | 继承 `True` | 默认带 stack |
| `ParamsException` | **`False`** | 客户端参数错误，stack 无价值，关掉避免恶意刷接口日志膨胀 |
| `KillSwitchPausedException` | 继承 `True`（自定义子类可按需关） | 紧急停机有意为之，stack 帮助定位"在哪个业务环节被熔断" |

**异常包装链 ≠ 重复**：业务里 `try/except + raise from` 链路上的每个 `AppBaseException` 实例都记自己的 stack，这是异常传播的真实记录。例：

```
ERROR [RiskRejectedException] code=600002 ... at guard.py:87 ...
ERROR [IdempotencyConflictException] code=600003 ... at order.py:120 ...
```

是两个不同异常实例的两条日志，**不算重复**，反而提供了完整的传播链信息。

**抛错规范**：
- CRUD 层（`get` 不存在）→ 抛 `DBException(error_code=ErrorCode.NOT_FOUND)`
- Service 层业务规则违反 → 抛 `ServiceException(...)` 或具体子类
- 参数非法 → 抛 `ParamsException("xxx 不能为空")`
- 业务代码**禁止就地** `class XxxError(Exception)`，需要新语义在 `errors.py` 增子类

**关于 `ErrorCode.NOT_FOUND` 段位与 `DBException` 的语义解释**：`NOT_FOUND` 错误码是 `"400005"`（4xx 客户端错误段位），由 `DBException` 子类抛出 —— **段位 4xx vs 异常类 DBException** 不冲突：
- 段位 4xx 表达的是"**客户端可见的错误语义**"（资源不存在 = 客户端请求的资源没有）
- `DBException` 表达的是"**抛出位置的技术分层**"（CRUD 层抛）
- 两者从不同角度描述同一异常，segment 决定了前端如何展示（404 风格），分层决定了代码组织
- **重抛时禁止双记**：`except DBException: raise` 不要再 `logger.exception()`；需要补上下文用 `logger.error(..., extra={...})` 不要 raise 新异常

**唯一日志记录点（核心约束）**：
- **每个异常恰好 1 条 ERROR 日志，永不重复**
- `AppBaseException` 子类：`_auto_log` 在抛出点记一行，含定位 + request_id；全局 handler **不再 logger.error()**，仅做 JSON 响应转换
- 未识别的 `Exception`（非 `AppBaseException` 子类）：由全局 handler 兜底记一行 + 完整 traceback（详见 §4.6.5）
- traceback 不在 `auto_log` 里记（`__init__` 时 `sys.exc_info()` 为空），也不通过 handler 重复记 `AppBaseException`；如果排查需要完整调用栈，靠 `exc_file:exc_lineno` + 业务代码定位即可（pytest / debugger 可重现）

**测试静音**：`tests/conftest.py` 加 `monkeypatch.setattr(AppBaseException, "auto_log", False)`，避免 `pytest.raises` 触发的日志污染输出。

#### 4.6.4 `@api_response()` 装饰器

装饰器只负责"成功响应自动包装 `response_base.success(data)`" + "异常分类日志"；不在装饰器里捕获并转换异常，异常向上抛给全局 exception handler。

```python
# src/common/api_response.py
def api_response(schema: Any = None) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Response:
            raw = fn(*args, **kwargs)                  # 业务异常直接抛出，由 handler 处理
            payload = to_schema(raw, schema)            # ORM → Pydantic 自动转
            return response_base.success(data=payload)
        return wrapper
    return decorator


def to_schema(raw: Any, schema: type[BaseModel] | None) -> Any:
    """ORM → Pydantic 自动转换。支持 None / dict / BaseModel / ORM 实例 / list / Paginated。

    schema 由 controller 函数签名的返回类型注入，或显式传给装饰器：
        @api_response(schema=PositionRead)
    """
    if raw is None or schema is None:
        return raw
    if isinstance(raw, BaseModel):
        return raw                                      # 已经是 Pydantic schema
    if isinstance(raw, list):
        return [schema.model_validate(item) for item in raw]
    return schema.model_validate(raw)                   # ORM model → Pydantic
```

注：装饰器**不再 try/except** —— 业务异常的日志由 `AppBaseException._auto_log` 自记，未识别异常由全局 exception handler 兜底（详见 §4.6.5）。装饰器只做"成功响应包装"。

#### 4.6.5 全局 Exception Handler（`src/common/exception/exception_handler.py`）

**唯一日志原则**：handler 仅在异常**没有 auto_log**（即非 `AppBaseException` 子类）时记日志，避免重复。

| Handler | 处理对象 | 是否记日志 | 行为 |
|---------|----------|----------|------|
| `AppBaseException` | 所有自定义业务异常 | ❌ **不记**（auto_log 已记） | HTTP 200 + body `{success: false, code, message, request_id}` |
| `RequestValidationError` | FastAPI 请求体校验 | ⚠️ INFO（非 error，客户端问题） | HTTP 200 + `VALIDATION_ERROR`，dev 环境携带完整 errors 列表 |
| `ValidationError` | Pydantic 模型校验 | ⚠️ INFO | 同上 |
| `ValueError` | 业务参数非法 | ⚠️ INFO | HTTP 200 + `PARAM_ERROR` |
| `AssertionError` | 断言失败 | ✅ ERROR + traceback | dev 回显 + 记 traceback；prod 返回 `SYS_ERROR` + 记 traceback |
| `HTTPException` | Starlette HTTP 异常（如 401/404 路径） | ❌ 不记（HTTP 标准语义） | 保留 HTTP 状态码，body 套 Response 形态 |
| `Exception` | 未识别异常兜底 | ✅ ERROR + traceback | 记完整 traceback；prod 返回 `SYS_ERROR` |

```python
# AppBaseException：仅 JSON 转换，不记日志
@app.exception_handler(AppBaseException)
async def app_exc_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "data": None,
            "request_id": current_request_id(),
        },
    )

# current_request_id() 来自 src/utils/request_id.py：
# from asgi_correlation_id import correlation_id
# def get_request_id() -> str | None:
#     """HTTP 链路返回 32 字符 hex（UUID 去横线）；scheduler 链路无值返 None"""
#     return correlation_id.get()
# def current_request_id() -> str: return get_request_id() or "-"

# 未识别异常：记 ERROR + traceback（这类没有 auto_log）
@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "[Unhandled] %s %s — %s",
        request.method, request.url.path, str(exc),
        exc_info=exc,                    # 完整 traceback
        extra={"request_id": current_request_id(), "method": request.method, "path": request.url.path},
    )
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "code": ErrorCode.SYS_ERROR.code,
            "message": ErrorCode.SYS_ERROR.msg,
            "data": None,
            "request_id": current_request_id(),
        },
    )
```

**关键设计**：
- 业务异常都 HTTP 200 + body 区分，前端按 `success` / `code` 判断
- 一个异常 = 一条日志：`AppBaseException` 由 auto_log 在 raise 行记；未识别 `Exception` 由 handler 在捕获点记（含 traceback）
- scheduler 进程的任务消费循环遵循同样规则（在 except 块内仅对未识别 `Exception` 用 `logger.error(..., exc_info=exc)`，对 `AppBaseException` 子类直接吞掉异常 / 落库失败状态，不再记日志）

#### 4.6.6 前端配套升级

前端 `fetch` / `axios` 封装层需调整：
- 所有响应都 HTTP 200（除真正的传输错误）
- 解析逻辑：先看 `response.success`：true → 取 `response.data`；false → 按 `response.code` 业务分类（401 跳登录、429 限流提示、其他显示 `response.message`）
- WebSocket payload **不走 `Response[T]` envelope**（事件直接推送）

### 4.7 中间件栈

```python
# 注册顺序（add_middleware 是从内到外）：
app.add_middleware(ErrorLoggingMiddleware)            # 内层：捕获未处理异常 + 日志
app.add_middleware(RequestLoggingMiddleware)          # 中层：req/resp 时间 + 路径日志
if configs.ENABLE_CORS:
    app.add_middleware(CORSMiddleware, ...)

from src.utils.uuid import get_uuid_without_hyphen     # 复用现有 utils
app.add_middleware(
    CorrelationIdMiddleware,                          # 最外层：X-Request-ID 注入
    header_name="X-Request-ID",
    generator=get_uuid_without_hyphen,                # 强制：UUID 去横线版（32 字符 hex）
    update_request_header=True,
)
```

`request_id`（HTTP 头 `X-Request-ID`）通过 `asgi-correlation-id` 中间件注入 ContextVar，在请求生命周期内任意位置可读（`src.utils.request_id.get_request_id()`），注入到 `Response[T]` body 与所有日志的 `extra` 字段中。

**`request_id` 格式约定（强制）**：
- **UUID4 去横线**（`uuid4().hex` / `get_uuid_without_hyphen()`），32 字符 hex 字符串
- 例：`550e8400e29b41d4a716446655440000`（不是 `550e8400-e29b-41d4-a716-446655440000`）
- 与项目现有主键生成器一致；前端 / 日志聚合系统 grep 时无需处理横线
- 客户端如果在 `X-Request-ID` 头主动传入，需自行保证格式一致（中间件不强校验，但日志会反映传入值）

**与业务幂等键 `trace_id` 的区分**（项目内严格遵守）：

| 字段 | 用途 | 来源 / 生成 | 类型 |
|------|------|-----------|------|
| `request_id` | HTTP 请求链路追踪 | CorrelationId 中间件，每次请求生成 UUID | str（uuid4） |
| `Order.trace_id`（业务幂等键） | 防重复下单 | `SHA256(decision_id:symbol:action)` | `String(64)` |

两者不互相替代、不互相覆盖；命名清晰避免歧义。

### 4.8 Scheduler 进程

scheduler 部署为 docker-compose 的单容器（`replicas: 1`），不引入 leader 选举。**单 Python 进程同时承担两个职责**：APScheduler（后台线程跑定时任务）+ Redis BRPOP（主线程阻塞消费异步任务队列）。

#### 4.8.1 `scripts/start_scheduler.py`

```python
from src.utils.log import init_logger
init_logger("scheduler", "scheduler.log")

import json
import logging
import signal
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from src.configs import configs
from src.db.session import get_db_session
from src.utils.redis import get_redis_client

logger = logging.getLogger("scheduler")
_stop_flag = threading.Event()


def _setup_scheduler() -> BackgroundScheduler:
    """启动 APScheduler 后台线程，注册定时任务。"""
    scheduler = BackgroundScheduler(
        jobstores={
            "default": SQLAlchemyJobStore(
                url=configs.db_uri,
                tablename=configs.APSCHEDULER_JOBS_TABLE,
            ),
        },
        job_defaults={
            "coalesce": True,           # 错过的多次触发合并为 1 次
            "misfire_grace_time": 60,   # 容忍 60s misfire
            "max_instances": 1,         # 同一 job 不并发（避免策略循环重叠）
        },
    )

    from src.schedulers.strategy_pipeline_scanner import strategy_pipeline_job
    from src.schedulers.position_monitor_scanner import position_monitor_job

    scheduler.add_job(
        strategy_pipeline_job, "interval",
        minutes=configs.STRATEGY_LOOP_INTERVAL_MINUTES,
        id="strategy_loop", replace_existing=True,
    )
    scheduler.add_job(
        position_monitor_job, "interval",
        seconds=configs.POSITION_MONITOR_INTERVAL_SECONDS,
        id="position_monitor", replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started in background thread")
    return scheduler


def _consume_task_queue() -> None:
    """主线程阻塞消费 Redis 异步任务队列。"""
    from src.services.task_dispatcher import task_dispatcher_service

    redis_client = get_redis_client()
    queue_key = configs.TASK_QUEUE_KEY  # 默认 "alphapilot:tasks"

    logger.info("Task queue consumer started; queue=%s", queue_key)
    while not _stop_flag.is_set():
        try:
            # 短 timeout 让循环能定期感知 stop_flag，便于 graceful shutdown
            item = redis_client.brpop(queue_key, timeout=1)
            if item is None:
                continue
            task = json.loads(item[1])
            with get_db_session() as session:
                task_dispatcher_service.execute(session, task)
        except Exception:
            # 仅捕获未识别异常 + 兜底记一次（AppBaseException 已 auto_log）
            logger.exception("task queue loop unhandled error")
            time.sleep(1)  # 避免疯狂重试


def _recover_orphan_tasks() -> None:
    """启动时清理上次崩溃留下的孤儿任务。"""
    from src.services.task_dispatcher import task_dispatcher_service
    with get_db_session() as session:
        task_dispatcher_service.recover_orphans(session)


def _install_signal_handlers() -> None:
    def _on_signal(*_):
        logger.info("Received signal, exiting gracefully...")
        _stop_flag.set()
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)


def _start_event_shuttle() -> threading.Thread:
    """启动事件总线 outbox → Redis Pub/Sub 推送 daemon thread（详见 §4.8.3）"""
    from src.schedulers.event_shuttle import event_shuttle_loop
    t = threading.Thread(target=event_shuttle_loop, args=(_stop_flag,),
                         name="event-shuttle", daemon=True)
    t.start()
    logger.info("EventShuttle daemon thread started")
    return t


def main() -> None:
    _install_signal_handlers()
    _recover_orphan_tasks()
    scheduler = _setup_scheduler()
    shuttle = _start_event_shuttle()
    try:
        _consume_task_queue()       # 主线程阻塞 BRPOP
    finally:
        # 收到 SIGTERM → stop_flag 已 set →
        # 1. 主循环退出（不再 BRPOP 取新任务）
        # 2. 当前正在执行的 BRPOP 任务（如有）继续跑，直到 task_dispatcher.execute() 返回
        # 3. APScheduler shutdown(wait=True)：等待运行中的 job（如策略循环）执行完
        #    避免策略循环跑到一半被强制中断（半完成状态可能留下不一致数据）
        # 4. EventShuttle daemon thread：daemon=True 在主进程退出时被 kill，
        #    join(timeout=5) 给它 5 秒优雅窗口（让最后一批 outbox 推送完成）
        # 5. 整个进程在 docker stop_grace_period (60s) 内完成上述步骤；超时被 SIGKILL
        scheduler.shutdown(wait=True)              # 等 APScheduler in-flight job 完成
        shuttle.join(timeout=5)                    # 给 EventShuttle 5s 优雅退出
        logger.info("Scheduler container exiting")


if __name__ == "__main__":
    main()
```

**关键点**：
- **`BackgroundScheduler`（不是 `BlockingScheduler`）**：APScheduler 在后台线程跑，主线程才能跑 `_consume_task_queue` 阻塞 BRPOP
- **同一 Python 进程三个角色**：APScheduler 定时任务（后台线程）+ EventShuttle outbox 推送（daemon thread）+ Redis BRPOP 任务消费（主线程），共享同一个 SQLAlchemy engine 与 Redis 连接池
- **graceful shutdown 策略**（Docker `stop_grace_period: 60s`）：
  1. SIGTERM 触发 `_stop_flag.set()`
  2. BRPOP `timeout=1` 让主循环循环感知 `stop_flag`，**不再取新任务**
  3. 当前正在跑的任务（如有）继续跑完，**不主动中断**（保任务原子性）
  4. 60 秒内能跑完 → 干净退出
  5. 60 秒不完成 → Docker 发 SIGKILL → 任务在 DB 里残留 `running` 状态 → 下次启动 `_recover_orphan_tasks` 标 `failed`，**人工 review 决定是否重试**（符合"交易系统不自动重试"哲学）
- `replace_existing=True`：每次启动覆盖 PG `apscheduler_jobs` 表里的 job 定义
- `apscheduler_jobs` 表由 SQLAlchemyJobStore 自动建表；alembic 通过 `env.py::include_object` 排除该表

```python
# src/db/migrations/env.py — 排除 apscheduler_jobs
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name == "apscheduler_jobs":
        return False  # 该表由 SQLAlchemyJobStore 自动管理，不进 alembic
    return True

context.configure(target_metadata=Base.metadata, include_object=include_object, ...)
```

#### 4.8.2 EventShuttle（outbox → Redis Pub/Sub 推送）

业务 service 调 `event_bus_service.publish(session, event)` **只写 outbox 表**（与业务数据同事务 commit）。事件真正"广播"出去的动作由 **EventShuttle daemon thread** 完成 —— 单独跑在 scheduler 容器内（不是 api 容器，避免 N 个 worker 重复扫表）。

```python
# src/schedulers/event_shuttle.py
import json
import logging
import threading
import time

from src.configs import configs
from src.cruds import outbox_crud
from src.db.session import get_db_session
from src.utils.redis import get_redis_client

logger = logging.getLogger("scheduler.event_shuttle")
SHUTTLE_BATCH_SIZE = 50
SHUTTLE_IDLE_SLEEP = 0.5            # 无待发事件时休眠 500ms（低延迟 + 低 CPU）


def event_shuttle_loop(stop_flag: threading.Event) -> None:
    """outbox 表 → Redis Pub/Sub 推送循环。
    在 scheduler 容器主进程的 daemon thread 内运行；进程退出时自动结束。
    """
    redis = get_redis_client()
    channel = configs.EVENT_BUS_CHANNEL          # 默认 "alphapilot:events"

    while not stop_flag.is_set():
        try:
            published = _shuttle_one_batch(redis, channel)
            if published == 0:
                # 无待发事件，短休眠让 CPU 空闲
                stop_flag.wait(SHUTTLE_IDLE_SLEEP)
        except Exception:
            logger.exception("event_shuttle loop unhandled error")
            stop_flag.wait(1)  # 出错短退避，避免疯狂打日志


def _shuttle_one_batch(redis, channel: str) -> int:
    """取一批 pending 事件 publish 到 Redis 后标 published。
    返回成功 publish 的事件数。
    """
    with get_db_session() as session:
        events = outbox_crud.find_pending(session, limit=SHUTTLE_BATCH_SIZE)
        if not events:
            return 0
        for event_row in events:
            try:
                redis.publish(channel, json.dumps({
                    "type": event_row.event_type,
                    "payload": event_row.payload,
                    "user_id": event_row.user_id,
                    "occurred_at": event_row.created_at.isoformat(),
                }, ensure_ascii=False))
                outbox_crud.mark_published(session, event_row.id)
            except Exception as e:
                outbox_crud.bump_failed_attempts(session, event_row.id, error=str(e))
                if event_row.failed_attempts + 1 >= configs.EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS:
                    outbox_crud.mark_dead_letter(session, event_row.id)
        session.commit()
        return len(events)
```

**outbox 表 schema 关键字段**（沿用现有，确认 schema）：

```python
class Outbox(Base, TradingModeMixin):
    id: Mapped[int]                              # BigInt autoincrement
    event_type: Mapped[str]                       # 事件类名（StrategyDecisionEvent 等）
    payload: Mapped[dict]                         # JSONB 事件载荷
    user_id: Mapped[int | None]                   # 用于 ws 路由
    status: Mapped[str]                           # pending/published/dead_letter
    failed_attempts: Mapped[int]                  # 失败次数（达 MAX 进死信）
    error: Mapped[str | None]                    # 最后一次失败原因
    created_at: Mapped[datetime]
    published_at: Mapped[datetime | None]
```

**EventShuttle 的设计权衡**：

| 维度 | 设计选择 | 理由 |
|------|---------|------|
| 进程归属 | scheduler 容器内 daemon thread | 单实例消费，避免 api 多 worker 重复扫表；不引入 funboost / Celery 这类重型框架 |
| 触发机制 | while loop + idle sleep 500ms | 实时性接近毫秒级；空闲时 CPU < 1% |
| 失败重试 | `bump_failed_attempts` + max 后进 dead_letter | 不无限重试（Redis 长期不可用时不打爆日志）；dead_letter 由人工 / 后续 job 处理 |
| 与业务事务的关系 | service `publish()` 只写 outbox，与业务同事务 commit | 业务回滚时事件自动回滚；EventShuttle 异步推 → 至少一次语义 |
| 顺序性 | 不保证全局顺序 | 同一 user_id 的事件按 outbox.id 顺序扫，但 Redis publish 后 ws 端无强顺序保证 |
| 死信处理 | `outbox.status=dead_letter`，定期人工 / job review | 不是高吞吐场景，dead_letter 量很少 |

**与原项目 `src/workers/event_shuttle.py` 的关系**：保留逻辑、迁移到 `src/schedulers/event_shuttle.py`，去除 lifespan 启动，改由 scheduler 容器主进程拉起。

#### 4.8.3 Scheduler 与业务的解耦

```python
# src/schedulers/strategy_pipeline_scanner.py
from src.db.session import get_db_session
from src.services.risk.kill_switch import kill_switch_service
from src.services.strategy.pipeline import strategy_pipeline_service

def strategy_pipeline_job() -> None:
    with get_db_session() as session:
        if kill_switch_service.is_paused(session):
            logger.info("kill_switch=paused; strategy_loop skipped")
            return
        try:
            strategy_pipeline_service.run_once(session)
        except Exception:
            logger.exception("strategy_loop error")
```

### 4.9 api 进程内的后台任务 / 定时任务（决策表）

scheduler 进程独占"持久化的定时任务执行权"，但 api 进程偶尔仍需处理"请求触发的后台工作"或"进程级轻量定时任务"。按场景区分四类，**禁止在 api 进程内启动 APScheduler**（避免与 scheduler 进程的 PG JobStore 职责混淆）：

| 场景 | 推荐方案 | 实现 |
|------|---------|------|
| **请求级 fire-and-forget**（写审计日志、发通知、清理临时文件，丢失可容忍） | FastAPI `BackgroundTasks` | `def endpoint(bg: BackgroundTasks): bg.add_task(send_notification, ...)`；响应立即返回，任务在同 worker 内的 asyncio executor 执行 |
| **HTTP 触发的耗时业务**（生成报告、批量平仓、回测，需持久化 + 可恢复） | **写任务请求表 → scheduler 扫表执行** | api 写一行 `task_requests`（status=pending）→ 立即返回 `task_id` → scheduler 周期 job 扫 pending 任务 → 执行 → 写结果到 `task_results` → api 通过 WebSocket 推完成事件 |
| **api 进程级定时任务**（WebSocket 心跳、连接清理、本地缓存刷新；与 HTTP 生命周期绑定） | `lifespan` 启动 `asyncio.create_task` | 与现有 Redis Pub/Sub 订阅同样模式；进程退出时自动取消 |
| **必须准时触发的定时任务**（策略循环、持仓监控、日报生成） | **全部归 scheduler 进程** | 注册到 `src/schedulers/*_scanner.py`，PG JobStore 持久化 |

#### 4.9.1 任务请求表方案（场景 2 详细）— Redis List 队列消费

适用于"用户点一个按钮触发耗时任务"，如**手动一键全平仓**、**手动重新跑日报**。

**架构**：api 提交时**双写**（PG `task_requests` 表持久化 + Redis List 实时通知）→ scheduler 容器主线程 BRPOP 阻塞消费（毫秒级实时性）→ 执行结果写回 `task_requests` 表 + 通过 `event_bus_service` 推 WebSocket 事件。

```python
# src/models/task_request.py
class TaskRequest(Base, TradingModeMixin):           # ← 任务有交易环境上下文，必须按 testnet/mainnet 隔离
    __tablename__ = "task_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    # 例："close_all" / "regenerate_report" / "export_trades" / "backfill_klines"
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), index=True, default="pending")
    # 状态机：pending → running → done / failed
    progress: Mapped[int] = mapped_column(Integer, default=0)              # 0-100
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # created_at / updated_at 由 Base 提供
```

```python
# src/services/task_dispatcher.py（编排服务）
class TaskDispatcherService:
    HANDLERS: dict[str, Callable[[Session, int, dict], dict]] = {
        "close_all": _handle_close_all,
        "regenerate_report": _handle_regenerate_report,
        "export_trades": _handle_export_trades,
        # ...
    }

    def submit(self, session: Session, task_type: str, payload: dict, user_id: int,
               trading_mode: str) -> int:
        """api 调用：双写 PG 表 + Redis 队列。"""
        req = task_request_crud.add(
            session,
            task_type=task_type, payload=payload, status="pending",
            requested_by=user_id, trading_mode=trading_mode,
        )
        session.commit()
        get_redis_client().lpush(
            configs.TASK_QUEUE_KEY,
            json.dumps({"task_id": req.id, "task_type": task_type, "payload": payload}),
        )
        return req.id

    def execute(self, session: Session, task: dict) -> None:
        """scheduler 容器主线程从 BRPOP 拿到一条任务后调用，串行执行。"""
        task_id = task["task_id"]
        handler = self.HANDLERS.get(task["task_type"])
        if handler is None:
            task_request_crud.mark_failed(session, task_id, error=f"unknown task_type: {task['task_type']}")
            session.commit()
            return

        # 标记 running + 发"开始"事件
        task_request_crud.mark_running(session, task_id, started_at=TimeUtils.now())
        event_bus_service.publish(session, TaskStateChangedEvent(
            task_id=task_id, status="running",
            user_id=task["payload"].get("user_id"),
        ))
        session.commit()

        try:
            result = handler(session, task_id, task["payload"])
            task_request_crud.mark_done(session, task_id, result=result, finished_at=TimeUtils.now())
            event_bus_service.publish(session, TaskStateChangedEvent(
                task_id=task_id, status="done", result=result,
                user_id=task["payload"].get("user_id"),
            ))
        except ServiceException as exc:
            task_request_crud.mark_failed(session, task_id, error=exc.message, finished_at=TimeUtils.now())
            event_bus_service.publish(session, TaskStateChangedEvent(
                task_id=task_id, status="failed", error=exc.message,
                user_id=task["payload"].get("user_id"),
            ))
        except Exception as exc:
            # 未识别异常：log 已由全局未识别异常 handler / scheduler 主循环兜底
            task_request_crud.mark_failed(session, task_id, error="系统错误", finished_at=TimeUtils.now())
            event_bus_service.publish(session, TaskStateChangedEvent(
                task_id=task_id, status="failed", error="系统错误",
                user_id=task["payload"].get("user_id"),
            ))
        session.commit()

    def recover_orphans(self, session: Session) -> None:
        """scheduler 启动时清理孤儿任务。
        - status=pending：上次写表后崩在 LPUSH 之前 / Redis 队列丢消息 → 重新推回队列
        - status=running：上次崩在执行中 → 标 failed（交易系统不自动重试，人工 review）
        """
        redis_client = get_redis_client()
        pending = task_request_crud.find_by_status(session, ["pending"])
        for req in pending:
            redis_client.lpush(
                configs.TASK_QUEUE_KEY,
                json.dumps({"task_id": req.id, "task_type": req.task_type, "payload": req.payload}),
            )
            logger.info("Recovered orphan pending task %d into queue", req.id)

        affected = task_request_crud.bulk_mark_failed(
            session, status_in=["running"],
            error="scheduler restart, manual retry needed",
        )
        if affected:
            logger.warning("Marked %d orphan running tasks as failed", affected)
        session.commit()


task_dispatcher_service = TaskDispatcherService()


# Handler 示例（含进度回调）
def _handle_close_all(session: Session, task_id: int, payload: dict) -> dict:
    user_id = payload["user_id"]
    positions = position_crud.get_open_positions(session, user_id=user_id)
    total = len(positions)
    results: list[dict] = []
    for i, pos in enumerate(positions, 1):
        try:
            order = order_execution_service.close_manual(session, pos.id, user_id=user_id)
            results.append({"position_id": pos.id, "status": "closed", "order_id": order.id})
        except ServiceException as exc:
            results.append({"position_id": pos.id, "status": "failed", "error": exc.message})
        progress = int(i / total * 100)
        task_request_crud.update_progress(session, task_id, progress=progress)
        event_bus_service.publish(session, TaskProgressEvent(
            task_id=task_id, progress=progress, current_item=results[-1], user_id=user_id,
        ))
        session.commit()
    return {"total": total, "closed": sum(1 for r in results if r["status"] == "closed"), "results": results}
```

```python
# src/controllers/api/v1/execution/positions.py — api 提交任务
@router.post("/close-all", response_model=Response[CloseAllSubmitOut])
@api_response()
def submit_close_all(session: CurrentSession, current_user: CurrentUser) -> CloseAllSubmitOut:
    task_id = task_dispatcher_service.submit(
        session, task_type="close_all",
        payload={"user_id": current_user.id},
        user_id=current_user.id,
        trading_mode=current_user.current_trading_mode,
    )
    return CloseAllSubmitOut(task_id=task_id, status="queued")


# src/controllers/api/v1/system/tasks.py — 兜底状态查询
@router.get("/tasks/{task_id}", response_model=Response[TaskStatusRead])
@api_response()
def get_task_status(task_id: int, session: CurrentSession) -> TaskStatusRead:
    req = task_request_crud.get(session, task_id)         # 不存在抛 DBException(NOT_FOUND)
    return TaskStatusRead.model_validate(req)
```

**收益**：
- 实时性：BRPOP 毫秒级响应（vs 扫表 5 秒延迟）
- 持久化：PG `task_requests` 表是唯一权威（任务结果可查、可历史回看）
- 容错：api 推 Redis 失败时表里仍是 `pending`，scheduler 启动时 `recover_orphans` 自动重推
- 不自动重试：`running` 孤儿一律标 `failed`（符合"交易系统失败必须人工 review"哲学）
- 单一执行通道（scheduler 单容器）= 无并发冲突 = 不需要分布式锁

**与现有 `src/events/{outbox,inbox}/`（业务事件总线）的区分**：
- **业务事件**（订单成交 / 风控触发 / 决策完成）→ outbox 表 + EventShuttle 推 Redis Pub/Sub → ws 广播
- **业务任务**（一键全平仓 / 生成日报 / 导出 CSV）→ task_requests 表 + Redis List 队列 → scheduler 消费执行
- 两者数据流与目的不同，不强行合并。但都遵循「PG 表 = SSOT，Redis = 实时传输通道」的统一原则。

#### 4.9.2 BackgroundTasks 方案（场景 1 详细）

适用于"丢失可容忍 + 不需持久化"的轻任务：

```python
@router.post("/login")
@api_response()
def login(body: LoginCreate, bg: BackgroundTasks, session: CurrentSession) -> LoginOut:
    user = auth_service.authenticate(session, body.email, body.password)
    bg.add_task(audit_log_service.record_login, user.id, ip=body.client_ip)  # 后台执行
    return auth_service.issue_token(user)
```

⚠️ **限制**：
- 任务在响应它的 worker 内执行；该 worker crash 任务丢
- 不要执行长任务（> 5s）；长任务用 4.9.1
- 不要在 BackgroundTasks 里 commit 业务数据；commit 应该已经在 endpoint 同步段完成

### 4.10 日志 formatter 配置（让 extra 字段真正显示出来）

异常 `_auto_log` 在 `extra` 里输出 `request_id` / `exc_class` / `exc_code` 等字段，**只有 logger formatter 配置消费这些字段时才会出现在日志输出里**。本节给出统一 formatter 与 ContextFilter，确保字段不丢。

```python
# src/utils/log.py
import logging
from src.utils.request_id import get_request_id


class ContextFilter(logging.Filter):
    """为每条 log record 自动注入 request_id；缺失则填 '-'。"""
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id() or "-"
        return True


LOG_FORMAT = (
    "%(asctime)s %(levelname)-8s [%(name)s] "
    "request_id=%(request_id)s "
    "%(filename)s:%(lineno)d %(funcName)s | %(message)s"
)


def init_logger(name: str = "app", file_name: str | None = None) -> None:
    """统一日志初始化入口，api/scheduler 都调用一次。"""
    fmt = logging.Formatter(LOG_FORMAT)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if file_name:
        handlers.append(logging.FileHandler(f"logs/{file_name}", encoding="utf-8"))
    for h in handlers:
        h.setFormatter(fmt)
        h.addFilter(ContextFilter())                # 关键：让 %(request_id)s 永远有值
    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

**约定**：
- formatter 强制包含 `request_id` 字段（`%(request_id)s`）
- 业务代码调 `logger.info("...", extra={"order_id": 1234})` 添加结构化字段
- 异常 `_auto_log` 的 `extra` 字段（`exc_class` / `exc_code` 等）暂不进入文本格式（避免行太长），**只通过 JSON 日志聚合系统（如 Loki / ES）按字段查询**

### 4.11 WebSocket（多 worker 兼容设计）

api 多 worker 场景下，每个 worker 进程独立维护 WebSocket 连接 + 独立订阅 Redis Pub/Sub。**不需要"全局连接表"**，因为每个 ws 连接天然只属于一个 worker（接收 upgrade 请求的那个）。多个 worker 各自订阅 Redis 同一 channel 不会重复推送给同一连接（因为每个连接只在一个 worker 内）。

```python
# src/services/ws_manager.py
class WSConnectionManager:
    """单 worker 进程内的 WebSocket 连接管理。多 worker = 多个独立 Manager 实例。"""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)  # user_id → ws set

    async def register(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[user_id].add(ws)

    def unregister(self, user_id: int, ws: WebSocket) -> None:
        self._connections.get(user_id, set()).discard(ws)

    async def broadcast_to_user(self, user_id: int, event: dict) -> None:
        """向指定用户的所有连接（多个浏览器 tab）推送事件。本 worker 内的连接才推；
        其它 worker 收到同一 Redis 消息会推自己 worker 内的连接。"""
        dead: list[WebSocket] = []
        for ws in self._connections.get(user_id, set()):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[user_id].discard(ws)


ws_manager = WSConnectionManager()


# src/controllers/system/websocket.py
@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket, current_user: WSAuthUser):
    await ws_manager.register(current_user.id, ws)
    try:
        while True:
            await ws.receive_text()                # keepalive / 客户端心跳
    except WebSocketDisconnect:
        ws_manager.unregister(current_user.id, ws)


# src/app.py — lifespan 启动 Redis 订阅协程（每个 worker 一份）
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(redis_to_ws_broadcaster())
    try:
        yield
    finally:
        task.cancel()


async def redis_to_ws_broadcaster() -> None:
    """订阅 Redis Pub/Sub，将事件分发到本 worker 的 WebSocket 连接。"""
    pubsub = await get_async_redis().pubsub()
    await pubsub.subscribe("alphapilot:events")
    async for msg in pubsub.listen():
        if msg.get("type") != "message":
            continue
        event = json.loads(msg["data"])
        user_id = event.get("user_id")
        if user_id is not None:
            await ws_manager.broadcast_to_user(user_id, event)
```

**WebSocket payload 不走 `Response[T]` envelope**（仅 HTTP 走 envelope），直接推送事件结构：
```json
{"type": "task_state_changed", "task_id": 123, "status": "done", "result": {...}, "user_id": 1, "occurred_at": "..."}
```

---

## 5. 数据流：完整策略循环示例

展示 B-Hybrid 下"跨领域编排"的代码长什么样。

```python
# src/services/strategy/pipeline.py
from src.cruds import (
    kline_crud, indicator_crud, regime_crud, position_crud,
    decision_crud, order_crud, outbox_crud, account_snapshot_crud,
)
from src.services.execution.market_data import market_data_service
from src.services.execution.account_state import account_state_service
from src.services.execution.execution_guard import execution_guard_service
from src.services.execution.order_execution import order_execution_service
from src.services.insight.indicators import indicators_service
from src.services.insight.regime import regime_service
from src.services.strategy.decision_engine import decision_engine_service
from src.services.event_bus import event_bus_service

class StrategyPipelineService:
    def run_once(self, session: Session) -> None:
        for symbol in self.pipeline_symbols():
            for tf in self.pipeline_timeframes():
                self._run_symbol(session, symbol, tf)

    def _run_symbol(self, session: Session, symbol: str, tf: str) -> None:
        # 1. 拉行情 (execution.market_data)
        market_data_service.fetch_and_store(session, symbol, tf)
        # 2. 算指标 (insight.indicators)
        indicators = indicators_service.compute_latest(session, symbol, tf)
        # 3. 判定市场状态 (insight.regime)
        regime = regime_service.detect(session, indicators)
        # 4. 抓 context (execution.account + position)
        account = account_state_service.get_latest(session)
        positions = position_crud.get_open_positions(session, symbol)
        # 5. 决策 (strategy.decision_engine)
        decision = decision_engine_service.decide(
            session, symbol=symbol, tf=tf,
            indicators=indicators, regime=regime,
            account=account, positions=positions,
        )
        # 6. 风控 (execution.guard)
        guard_result = execution_guard_service.check(session, decision)
        if guard_result.rejected:
            return
        # 7. 执行 (execution.order_execution)
        if decision.action in {"OPEN_LONG"}:
            order_execution_service.execute_decision(session, decision)
        # 8. 写事件 (event_bus / outbox)
        event_bus_service.publish(session, StrategyDecisionEvent(...))

strategy_pipeline_service = StrategyPipelineService()
```

**观察点**：
- 跨领域 import 集中在 `pipeline.py` 一个文件，**编排可见**
- 各 service 内部**不互相 import 跨领域 service**（`order_execution` 不 import `decision_engine`）
- cruds 是数据访问的统一入口，无领域感

---

## 6. 五阶段推进路线

### 阶段 1：基础设施层（无业务影响）

**范围**：
- 拆 `src/db/{engines,session,migrate}.py`
- 配置类拆 8 个子类多继承（`src/configs/app_configs.py` 重写）
- 引入 `src/common/{response,exception,pagination,enums,constants,schema,api_response}/`（**仅建立工具，不强制使用**）
- 引入 `src/utils/{log,redis,time,uuid,request_id,json,serializers}/`
- 引入 `src/middleware/{request_logging,error_logging}/`
- **`src/app/app.py` 提级为 `src/app.py`**（FastAPI 应用工厂；模板规定 src 内唯一启动文件就是 `src/app.py`）；保留 `src/app/` 子目录暂存 `routers/` 等文件，阶段 4 重组 controllers 时再清理
- `src/app.py` 中间件栈注入 CorrelationId / RequestLogging / ErrorLogging（**响应体格式 / 异常处理保持当前行为**，仅注入 request_id 与 access log）
- 现有 `src/shared/db.py` 改成转发 wrapper（指向 `src/db/session.py`），逐步废弃

**验收**：
- 所有现有测试全绿（53 通过）
- 启动 + 健康检查 OK
- HTTP 行为零变化（前端无感知）

**回滚**：单 PR，revert 即可

### 阶段 2：DB 层扁平化 + 主键升级

**范围**：
- `shared/models/` → `src/models/`（一实体一文件，~17 个）；每个 model 第一字段为 `id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)`
- `Base` 类仅保留通用字段 `enable_flag / delete_flag / created_at / updated_at`；`trading_mode` 通过 `TradingModeMixin` 显式继承（按 §4.2.3 的归属规则）
- 所有跨表关联列（`Order.position_id`、`Position.decision_id`、`Trade.decision_id`、`RiskEvent.decision_id` 等）改 `BigInteger`
- 引入 `src/cruds/base_crud.py` + 一实体一 crud（~17 个）；CRUD 层不存在抛 `DBException(NOT_FOUND)`
- `src/schemas/` 平铺迁移
- Alembic 配置迁移到 `src/db/alembic.ini`，**原 `backend/alembic.ini` 删除**
- **`migrations/versions/` 全量删除并重建**：`alembic revision --autogenerate -m "init schema with bigint pk"` 生成单个初始 migration
- service 层暂时保留旧调用方式（直接 `session.query(Model)`），但**新加方法必须走 cruds**

**验收**：
- 所有测试全绿（测试 fixture 中如有 hard-code String UUID 必须同步改 int）
- 干净 PG 数据库执行 `make init-db` + `alembic upgrade head` 跑通，所有表主键为 `BIGINT` + `IDENTITY` 自增
- `python -c "from src.models import *"` 不报错（显式 import 链完整）
- `tests/integration/` 集成测试在干净库 + 重建 migration 上全绿

**回滚**：单 PR，revert 代码 + 重建 dev/test 数据库（dev 阶段无生产数据，重建可接受）

### 阶段 3：业务层重组

**范围**：
- 现有 `src/{execution,insight,strategy,events,control,services,workers}/` 按 B-Hybrid 重组到 `src/services/{execution,insight,strategy,risk}/`
- 抽 `src/core/{exchange,llm,indicators,trace}/` 容纳无状态计算 / 外部客户端
- 现有 `src/workers/{strategy_loop,position_monitor,...}.py` 暂留，作为"调用 services/* 的薄壳"，不动 lifespan
- service 层全面切到 cruds 调用（不再裸 SQL）
- **业务事件类迁移**：现有 `src/events/contracts.py` 中的 `BaseEvent` 子类（`StrategyDecisionEvent` / `OrderCreatedEvent` / `RiskTriggeredEvent` 等）迁移到 `src/common/events.py`，命名按规范保持 `xxxEvent` 后缀，字段补齐 `user_id` / `request_id` / `occurred_at`；现有 `src/events/{bus,outbox,inbox,ids}.py` 重组为：
  - `src/services/event_bus.py`（编排）
  - `src/cruds/{outbox,inbox}_crud.py`（数据访问）
  - `src/schedulers/event_shuttle.py`（推送 daemon，阶段 5 启用，本阶段先迁代码不动调度）

**验收**：
- 所有测试全绿
- HTTP / WebSocket / scheduler 行为零变化
- `from src.events.*` 旧 import 路径全部清除（grep 验证）

**回滚**：单 PR，revert 即可（仅文件搬移 + import 路径变更）

### 阶段 4：响应/异常体系切换

**范围**：
- `src/app/routers/*` → `src/controllers/api/v1/{domain}/*`
- 所有 controller 加 `@api_response()` 装饰器，返回 `Response[T]`
- 引入业务异常树（`AppBaseException` / `ServiceException` / `DBException` / `ParamsException` + 业务专属如 `KillSwitchPausedException`）；现有 `HTTPException(404,...)` 全替换为对应异常（如 CRUD 不存在抛 `DBException(NOT_FOUND)`，业务规则违反抛 `ServiceException`）
- 注册全局 exception handler
- **前端 fetch 封装层同步升级**（解 `data` 字段、判 `code` 字段、处理 request_id 用于错误上报）
- 前端所有调用点 e2e 验证

**验收**：
- 所有后端测试全绿
- 前端单测 + e2e 跑通
- HTTP 响应格式按规范升级（手工测试覆盖关键接口：登录 / 持仓查询 / 平仓 / 决策列表 / 风控事件）

**回滚**：本阶段是真正的 breaking change，回滚需要前后端同时 revert；建议合并前在 dev 环境跑 24h 观察

### 阶段 5：scheduler 进程拆分 + APScheduler 持久化

**范围**：
- `scripts/start_api.py` + `scripts/start_scheduler.py` 创建
- `src/schedulers/{strategy_pipeline_scanner,position_monitor_scanner}.py` 创建
- APScheduler 切 `SQLAlchemyJobStore`（PostgreSQL `apscheduler_jobs` 表，由 SQLAlchemyJobStore 首次启动时自动建表；alembic `env.py` 用 `include_object` 排除该表）
- `src/app.py`（已在阶段 1 提级到位） lifespan 移除 scheduler 启动逻辑（仅保留 WebSocket 订阅 + admin bootstrap）
- `docker-compose.{local,dev-server,test,prod}.yml` 改造：
  - 原 `backend` service → `api` service（多 worker，`UVICORN_WORKER_NUM` 环境变量按部署环境配，dev=2 / prod=按 CPU）
  - 新增 `scheduler` service（单容器，`replicas: 1`、`restart: always`、**`stop_grace_period: 60s`**（与 `SCHEDULER_GRACEFUL_SHUTDOWN_SECONDS` 一致，给 SIGTERM 后的任务收尾窗口））
- `Makefile` 增加 `make dev-api` / `make dev-scheduler` 目标
- `scripts/deploy-dev.sh` 同步更新（拉镜像 + 启 api + 启 scheduler）
- 旧 `src/workers/*` 删除

**验收**：
- 所有测试全绿
- dev server 部署：api（多 worker） + scheduler（单容器）双 service 同时运行
- scheduler 容器重启后 job 状态从 `apscheduler_jobs` 表恢复（在 PG 里能看到 next_run_time 持续更新）
- WebSocket 多 worker 验证：用 2 个浏览器 tab 连 ws，触发一个事件，两个 tab 都收到（确保多 worker 各自订阅 + 各自广播工作正常）

**回滚**：本阶段涉及部署形态，回滚需更新 docker-compose 回到单 service + lifespan 启动 scheduler；建议合并前在 dev 跑 24h 观察

---

## 7. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 阶段 4 前端忘记升级，API 上线后前端报错 | 中 | 高 | 阶段 4 前后端同 PR 合并；dev 环境必须验证 e2e |
| Alembic 在阶段 2/5 自动生成迁移漏字段 | 中 | 高 | 每次 `alembic revision --autogenerate` 后必须人工 review；启用 `compare_type=True` |
| scheduler 单容器宕机导致定时任务停摆 | 低 | 中 | docker-compose `restart: always`；监控 scheduler 容器 `next_run_time` 字段是否定期更新 |
| APScheduler `SQLAlchemyJobStore` 与 alembic 自动生成冲突 | 低 | 中 | `apscheduler_jobs` 表不放在 SQLAlchemy `metadata` 内，`alembic env.py` 用 `include_object` 排除 |
| API 多 worker 时 WebSocket 广播丢失或重复 | 中 | 中 | 每个 worker 独立订阅 Redis Pub/Sub + 仅广播给本 worker 内连接（验证见阶段 5） |
| 阶段 3 重组导致 import 链路出现循环 | 低 | 中 | B-Hybrid 设计已规避（model 不跨包，service 跨领域 import 集中在 pipeline）；重组时按依赖顺序迁移 |
| 重构周期内 main 分支冻结 | — | 中 | 每阶段独立 PR、独立合并；阶段间允许业务侧 hotfix 走 main，重构分支定期 rebase |
| 测试覆盖不足导致重构期间隐性 bug | 中 | 高 | 每阶段 PR 必须新增至少 1 个集成测试 + 全部单测通过；阶段 4/5 必须在 dev 跑 24h 观察 |

---

## 8. 不在范围内（YAGNI）

- ❌ funboost / Redis Stream 异步任务框架
- ❌ 异步 SQLAlchemy / `asyncpg` / async 路由
- ❌ Phoenix LLM 追踪（`arize-phoenix-otel`）
- ❌ `msgspec` JSON 加速
- ❌ `nb_log` 日志库（保留 stdlib `logging`）
- ❌ supervisor 单镜像多进程（用 Docker Compose 多 service）
- ❌ 飞书 / lark 业务模块
- ❌ 业务行为变更（决策规则、风控阈值、执行链路全部不动）
- ❌ DB schema 重构（仅在阶段 5 加 `apscheduler_jobs` 表）
- ❌ 性能优化（连接池调参、慢查询、缓存策略）—— 重构稳定后另开任务
- ❌ 多策略并行 / 多账户 —— 未来需求

---

## 9. 验收清单（合并主分支前总验收）

- [ ] 所有 5 个阶段已合并
- [ ] `tests/` 全绿，单测 + 集成测试覆盖率 ≥ 当前水平
- [ ] 前端 e2e 通过
- [ ] dev server 上线运行 ≥ 24h，无异常
- [ ] `make dev-up` / `make dev-backend` / `make dev-scheduler` 一键启动
- [ ] `docs/worklog/` 每阶段有对应记录
- [ ] `CLAUDE.md` 项目记忆更新到反映新结构
- [ ] `.claude/memory/MEMORY.md` 索引更新
- [ ] `example.env` 与新 `AppConfig` 字段一致
- [ ] `docker-compose.*.yml` 与新进程模型一致

---

## 10. 项目规范文档（重要交付物）

本次重构最有价值的副产物之一是沉淀**一份属于 alpha-pilot 自己的工程规范**，让所有后续 AI 协作 / 新人开发都有"宪法"可循。规范文档与代码同步演进，**每一条规范都必须在代码里有落地的载体**（不写"墙上规范"）。

### 10.1 文档定位与路径

- **路径**：`docs/project.md`
- **定位**：alpha-pilot 项目的工程"宪法"，覆盖目录、命名、分层、API 契约、异常、DB、任务模型、Git 流程等
- **与现有文档关系**：
  - `CLAUDE.md`（项目入口）：在顶部新增强制项「**开始任何编码工作前，必须先读 `docs/project.md`**」
  - `.claude/memory/MEMORY.md`（会话记忆索引）：补一行 `[项目工程规范](../../docs/project.md)`
  - `docs/fastapi-project-template-v3.md`（外部模板原文）：保留作为参考来源，不替代 `project.md`
  - `docs/worklog/`（工程过程日志）：每阶段产出对应 worklog 文件，记录"做了什么 / 为什么 / 如何验证 / commit"

### 10.2 章节结构（一级目录）

```
docs/project.md
├── 0. 阅读须知
│   - 本文档地位（项目宪法）
│   - 适用范围（后端 + 前端约定的接口契约部分）
│   - 变更流程（必须 PR review）
├── 1. 项目结构
│   - B-Hybrid 目录布局图
│   - 各层职责边界（Controller / Service / CRUD / Core / Model）
│   - 文件命名规范（域路径 / 单复数 / 后缀）
├── 2. Python 环境与依赖
│   - Python 3.12 / uv / venv 位置
│   - PYTHONPATH 与 import 规则（src. 开头）
│   - 新增依赖工作流
├── 3. 配置体系
│   - pydantic-settings 多继承（8 个子配置类归属）
│   - example.env 同步规则
│   - 环境变量黑白名单
├── 4. 数据库规范
│   - 同步 SQLAlchemy（禁止 AsyncSession）
│   - Base + TradingModeMixin（trading_mode 归属规则表）
│   - 主键 BigInteger autoincrement，每个 model 第一字段
│   - 外键禁止 + index=True
│   - expire_on_commit=False + service 层 commit/refresh 规范
│   - Alembic 迁移规则（必须 alembic revision，禁止手写）
├── 5. 分层与命名规范（核心章节）
│   - 五层职责清单
│   - Controller / Service / CRUD / Core / Model / Schema 的类与文件命名
│   - Schema 命名规范表（Read / Create / Update / Out / Query）
│   - 禁用命名清单（VO / DTO / Res / Response / Schema）
│   - import 依赖方向规则（不允许跨领域 import service）
├── 6. API 契约
│   - Response[T] 结构与字段含义
│   - @api_response 装饰器使用
│   - HTTP 状态码 vs 业务 code 区分
│   - WebSocket payload 不走 envelope
│   - 错误码段位（0 / 400xxx / 500xxx / 600xxx 业务专属）
├── 7. 异常处理
│   - AppBaseException 树
│   - 抛错位置规范（CRUD 抛 DBException、Service 抛 ServiceException）
│   - 业务专属异常一律 errors.py 集中
│   - 禁止业务代码就地 class XxxError(Exception)
├── 8. 异步任务与定时任务
│   - api / scheduler 双容器交互模型图
│   - 任务持久化三层（PG / Redis List / WebSocket）
│   - task_requests 表协议与状态机
│   - 不自动重试原则（交易系统）
│   - api 进程禁止启动 APScheduler
│   - 4 类后台任务场景决策表
├── 9. 业务专属规范（alpha-pilot 特有）
│   - 交易模式隔离（trading_mode 字段）
│   - 幂等 trace_id 生成规则（SHA256(decision_id:symbol:action)）
│   - 风控不可被 LLM 覆盖
│   - LLM 兜底（解析失败一律 HOLD）
│   - kill_switch 检查点（每个 service 入口必须检查）
│   - 决策与订单的 ID 关联约定
├── 10. 日志与可观测性
│   - logger 命名 / 日志路径
│   - request_id 注入（HTTP 链路；与业务幂等 trace_id 区分）
│   - 异常分级（INFO / WARNING / ERROR）
│   - 不打印敏感字段（API key / token / 用户密码）
├── 11. 测试规范
│   - tests/unit / tests/integration 分层
│   - savepoint 隔离 fixture
│   - 测试命名 test_xxx_when_xxx_then_xxx
│   - 覆盖率门槛与 CI 集成
├── 12. Git 与发布流程
│   - commit message 中文，前缀 feat/fix/refactor/docs/test/chore
│   - 自动 push（CLAUDE.md 已有规则）
│   - worklog 路径与格式
│   - 阶段性 PR 拆分原则
├── 附录 A. 决策日志（与本 spec §2 对应）
│   - 不引入 funboost 的理由
│   - 选同步 session 的理由
│   - B-Hybrid 目录的理由
│   - 主键 BigInteger autoincrement 的理由
│   - xxxRead 命名的业界依据
├── 附录 B. AI 协作指南
│   - 每次任务开始前 AI 必读列表
│   - 常见反模式清单（VO / lazy load / 跨域 service import / async session）
│   - 如何提交 PR（commit / push / dev 部署 / worklog）
└── 附录 C. 模板差异说明
    - 与 docs/fastapi-project-template-v3.md 的差异表（PostgreSQL / 不引 funboost / id BigInt / 不强制单 worker 等）
```

### 10.3 产出节奏（与五阶段绑定）

文档**不在重构开始前一次性写完**，而是**每阶段交付时填充对应章节**，让规范来自代码而不是反过来：

| 阶段 | 该阶段产出的 `docs/project.md` 章节 |
|------|-----------------------------------|
| 阶段 1（基础设施） | §0 阅读须知 / §1 项目结构骨架 / §2 Python 环境 / §3 配置体系 / 附录 A 决策日志 v1 |
| 阶段 2（DB 层） | §4 数据库规范完整版 / §5 命名规范的 Model & CRUD 部分 |
| 阶段 3（业务层） | §5 命名规范的 Service & Core 部分 / §9 业务专属规范完整版 |
| 阶段 4（响应/异常） | §6 API 契约 / §7 异常处理 / §5 命名规范的 Schema 部分 |
| 阶段 5（进程拆分） | §8 异步任务 / §10 日志 / §11 测试 / §12 Git 流程 / 附录 B / 附录 C 完整版 |
| **合并主分支前** | `CLAUDE.md` 顶部加引用、`.claude/memory/MEMORY.md` 加链接，`docs/project.md` 定稿审 |

### 10.4 落地规则

- **每一条规范必须有代码示例**（正例 + 反例）
- **每一条规范必须有强制载体**（Linter 规则 / mypy 配置 / 测试 / code review checklist）
- **变更流程**：修改 `docs/project.md` 必须走 PR，且 PR 描述里说明"为何变更"+"对存量代码的影响"
- **AI 协作集成**：`CLAUDE.md` 顶部加：
  ```markdown
  ## 强制阅读
  开始任何编码工作前，必须读取以下文档：
  1. `docs/project.md` — 项目工程规范（宪法）
  2. `.claude/memory/MEMORY.md` — 会话记忆索引
  3. `CLAUDE.md` 本文 — 项目快速恢复指南
  ```

### 10.5 阶段完成验收增项

`§9 验收清单（合并主分支前总验收）` 增加：

- [ ] `docs/project.md` 全部章节填充完毕
- [ ] `CLAUDE.md` 顶部添加强制阅读引用
- [ ] `.claude/memory/MEMORY.md` 加 `docs/project.md` 链接
- [ ] 抽样验证：随机挑 3 条规范，对应代码确实落地（不是墙上规范）

---

## 11. 后续工作（不在本次重构内）

- 性能与可观测性章节落地（连接池监控、慢查询日志、应用层中间件计时）
- APScheduler `RedisJobStore` 实验（如 PG JobStore 出现锁竞争问题）
- 多策略并行架构（每个策略独立 pipeline + 独立持仓桶）
- 幂等 trace_id 升级到 Redis 缓存层（避免重复落库）

---

**文档结束**。请老板审阅；通过后将进入 `writing-plans` 流程产出实施计划。
