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
- **数据库 schema 零破坏**：本次重构不动表结构；所有 schema 变更走 `alembic revision`（CLAUDE.md 强制）
- **CLAUDE.md 工作流强制**：每阶段交付 = 编译通过 + 测试全绿 + commit + push + dev 部署验证 + worklog

---

## 2. 关键技术决策汇总

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 进程模型 | `web` + `scheduler` 双进程 | scheduler 与 HTTP 故障隔离，scheduler 失败不影响用户接口 |
| Session 模型 | 同步 SQLAlchemy `Session` | 与模板一致；交易系统优先正确性而非 I/O 并发 |
| 异步任务框架 | APScheduler，**不引入 funboost** | 单 Pod 场景下 funboost 是过度工程 |
| Job 元数据持久化 | `SQLAlchemyJobStore`（PostgreSQL `apscheduler_jobs` 表） | 重启不丢 job 状态；与业务库一致便于备份 |
| Scheduler 单实例锁 | Redis `SET NX EX` + Lua 原子释放 | 已有 Redis，轻量；不占 PG 连接池 |
| 目录布局 | **B-Hybrid**：DB 层扁平 + 业务层按领域聚合 | 见 §3.1 |
| 响应体系 | `Response[T]` 包装 + `@api_response` + 全局 exception handler | HTTP 状态码（传输层） + 业务 code（业务层）双轨 |
| 异常树 | `BizError` 基类 → `NotFoundError` / `ValidationError` / `PermissionError` / `ConflictError` / 业务专属异常 | 与 HTTP 状态码语义化对应，trace_id 自动注入 |
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
├── alembic.ini                             # 迁移到 src/db/alembic.ini（保留兼容入口或删除）
├── docker/
│   ├── Dockerfile.web
│   ├── Dockerfile.scheduler
│   └── entrypoint.sh
├── scripts/
│   ├── start_web.py                        # FastAPI 进程入口
│   ├── start_scheduler.py                  # APScheduler 进程入口
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
    │   └── leader_lock.py                  # Redis 分布式锁（SET NX EX + Lua 释放）
    │
    └── utils/
        ├── log.py                          # init_logger / get_logger
        ├── redis.py                        # redis_client + 锁工具
        ├── time.py                         # 北京时间工具
        ├── uuid.py
        ├── trace_id.py
        ├── json.py                         # 自定义 JSON 编解码（datetime/Enum/Decimal）
        └── serializers.py                  # FastAPI 响应类（如有特殊定制）
```

### 3.2 进程模型

```
┌──────────────────────────────────────────────────────────────────┐
│                       Docker Compose                              │
├──────────────────────────────┬───────────────────────────────────┤
│   web service                │   scheduler service                │
│   ----------------           │   ----------------                 │
│   入口: scripts/start_web.py │   入口: scripts/start_scheduler.py │
│                              │                                    │
│   职责:                       │   职责:                            │
│   - FastAPI HTTP 服务         │   - APScheduler 调度策略循环/监控  │
│   - WebSocket /ws            │   - 启动时通过 Redis 锁选 leader   │
│   - Redis Pub/Sub 订阅广播   │   - SQLAlchemyJobStore (PG)        │
│   - lifespan 不启动 scheduler│   - 业务直接执行（不分发到 worker）│
│                              │                                    │
│   uvicorn workers=1 (强约束) │   单进程持锁运行                   │
└──────────────────────────────┴───────────────────────────────────┘
                  ↓                              ↓
              ┌──────────────────────────────────────┐
              │  PostgreSQL 16  +  Redis 7           │
              │  - 业务库 + apscheduler_jobs 表      │
              │  - Pub/Sub + Leader 锁               │
              └──────────────────────────────────────┘
```

**关键约束**：
- `web` 进程 `uvicorn workers=1`（追踪器/调度器是进程级单例，多 worker 冲突）
- `web` 进程 `lifespan` 内**不再启动 APScheduler**（由 scheduler 进程独占）
- `scheduler` 进程**不引用 FastAPI**，直接通过 `get_db_session()` 调用 service 层
- 多 Pod 部署时：所有 web Pod 平等运行；所有 scheduler Pod 通过 Redis 锁选出唯一 leader 执行 job，其余 standby 轮询竞锁

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
class SchedulerConfig(BaseSettings):     # STRATEGY_LOOP_INTERVAL_MINUTES / POSITION_MONITOR_INTERVAL_SECONDS
                                         # SCHEDULER_LEADER_LOCK_KEY / SCHEDULER_LEADER_LOCK_TTL
                                         # APSCHEDULER_JOBS_TABLE
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

#### 4.2.3 `models/base.py` — 公共字段基类

```python
class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=get_uuid_without_hyphen)
    trading_mode: Mapped[str] = mapped_column(String(16), nullable=False, comment="testnet/mainnet 数据隔离")
    enable_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    delete_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=TimeUtils.now, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=TimeUtils.now, onupdate=TimeUtils.now)
```

注：alpha-pilot 现有模型已有 `trading_mode` 字段，本次对齐到 Base 基类（如果 schema 不一致需 `alembic revision`）。

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
- 命名规范：`get_xxx`（不存在抛错）/ `get_xxx_or_none`（不存在返 None）

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

### 4.5 Controller 层（`src/controllers/api/v1/{domain}/`）

```python
# src/controllers/api/v1/execution/positions.py
from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.db.session import CurrentSession
from src.schemas.position import PositionVO
from src.services.execution.order_execution import order_execution_service

router = APIRouter(prefix="/positions", tags=["execution.positions"])

@router.get("/{position_id}", response_model=Response[PositionVO])
@api_response()
def get_position(position_id: str, session: CurrentSession) -> PositionVO:
    position = position_crud.get(session, position_id)   # 不存在自动抛 NotFoundError
    return PositionVO.model_validate(position)

@router.post("/{position_id}/close", response_model=Response[PositionVO])
@api_response()
def close_position(position_id: str, session: CurrentSession) -> PositionVO:
    position = order_execution_service.close_position_manually(session, position_id)
    return PositionVO.model_validate(position)
```

**规范**：
- controller 只做参数校验 + service 调用 + DTO 转换；**禁止写业务逻辑**
- 所有 controller 函数加 `@api_response()` 装饰器；返回值就是 `data` 字段内容
- 业务异常通过抛 `BizError` 子类传递；HTTPException 不再使用

### 4.6 响应/异常体系

#### 4.6.1 `Response[T]` 结构

```python
class ResponseBase(BaseModel):
    code: int
    msg: str
    trace_id: str | None = None

class Response(ResponseBase, Generic[T]):
    data: T | None = None
```

#### 4.6.2 `@api_response()` 装饰器

装饰器**只负责包装成功响应**；业务异常一律由全局 exception handler 统一处理，装饰器内不捕获。

```python
def api_response():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = func(*args, **kwargs)  # 业务异常直接抛出，让 exception handler 处理
            return Response[Any](code=0, msg="OK", data=data, trace_id=current_trace_id())
        return wrapper
    return decorator
```

#### 4.6.3 异常树

```python
class BizError(Exception):
    code: int = 50000
    msg: str = "业务异常"
    http_status: int = 500

class NotFoundError(BizError):           # http=404, code=40400
class ValidationError(BizError):         # http=400, code=40000
class PermissionError(BizError):         # http=403, code=40300
class ConflictError(BizError):           # http=409, code=40900
class UnauthorizedError(BizError):       # http=401, code=40100

# 业务专属
class KillSwitchPausedError(BizError):   # http=503, code=53001
class RiskRejectedError(BizError):       # http=422, code=42201
class IdempotencyConflictError(BizError):# http=409, code=40901
class InsufficientBalanceError(BizError):# http=422, code=42202
```

#### 4.6.4 全局 Exception Handler

注册 4 类：
1. `BizError` → HTTP 状态码 = `exc.http_status`，body = `{"code": exc.code, "msg": exc.msg, "data": None, "trace_id": ...}`
2. `RequestValidationError`（FastAPI 校验失败）→ HTTP 422 + code=42200
3. `SQLAlchemyError` → HTTP 500 + code=50001 + 日志告警
4. `Exception` 未知异常 → HTTP 500 + code=50000 + trace_id 必填

```python
@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "msg": exc.msg, "data": None, "trace_id": current_trace_id()},
    )
```

#### 4.6.5 前端配套升级

前端 `fetch` / `axios` 封装层需调整：
- 成功响应：从 `response.json()` 改为 `response.json().data`
- 错误响应：从 `response.json().detail` 改为 `response.json().msg`，`error.code` 用业务码
- WebSocket payload **不包 `Response[T]`**（仅 HTTP 走 envelope，WebSocket 仍直接推送事件 payload）

### 4.7 中间件栈

```python
# 注册顺序（add_middleware 是从内到外）：
app.add_middleware(ErrorLoggingMiddleware)            # 内层：捕获未处理异常 + 日志
app.add_middleware(RequestLoggingMiddleware)          # 中层：req/resp 时间 + 路径日志
if configs.ENABLE_CORS:
    app.add_middleware(CORSMiddleware, ...)
app.add_middleware(CorrelationIdMiddleware,           # 最外层：X-Request-ID 注入
                   header_name="X-Request-ID",
                   update_request_header=True)
```

`trace_id`（`X-Request-ID`）通过 `starlette-context` 在请求生命周期内可读，注入到 `Response[T]` 与日志中。

### 4.8 Scheduler 进程

#### 4.8.1 `scripts/start_scheduler.py`

```python
from src.utils.log import init_logger
init_logger("scheduler", "scheduler.log")

from src.schedulers.leader_lock import RedisLeaderLock
from src.configs import configs
from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

def main():
    lock = RedisLeaderLock(
        key=configs.SCHEDULER_LEADER_LOCK_KEY,
        ttl_seconds=configs.SCHEDULER_LEADER_LOCK_TTL,
    )

    while True:
        if lock.acquire():
            try:
                run_scheduler_as_leader()
            finally:
                lock.release()
        else:
            time.sleep(5)  # standby loop

def run_scheduler_as_leader():
    scheduler = BlockingScheduler(
        jobstores={"default": SQLAlchemyJobStore(url=configs.db_uri,
                                                 tablename=configs.APSCHEDULER_JOBS_TABLE)},
        job_defaults={"coalesce": True, "misfire_grace_time": 60, "max_instances": 1},
    )
    from src.schedulers.strategy_pipeline_scanner import strategy_pipeline_job
    from src.schedulers.position_monitor_scanner import position_monitor_job

    scheduler.add_job(strategy_pipeline_job, "interval",
                      minutes=configs.STRATEGY_LOOP_INTERVAL_MINUTES,
                      id="strategy_loop", replace_existing=True)
    scheduler.add_job(position_monitor_job, "interval",
                      seconds=configs.POSITION_MONITOR_INTERVAL_SECONDS,
                      id="position_monitor", replace_existing=True)

    # 锁续期 daemon 线程：每 ttl/3 秒续期一次
    threading.Thread(target=lock.keep_alive_loop, daemon=True).start()

    scheduler.start()  # 阻塞
```

#### 4.8.2 `src/schedulers/leader_lock.py` — Redis 分布式锁

```python
class RedisLeaderLock:
    def __init__(self, key: str, ttl_seconds: int = 30):
        self.key = key
        self.ttl = ttl_seconds
        self.token = uuid4().hex          # 每个进程生成唯一 token，用于安全释放
        self.client = get_redis_client()

    def acquire(self) -> bool:
        return bool(self.client.set(self.key, self.token, nx=True, ex=self.ttl))

    def renew(self) -> bool:
        # Lua 原子化：仅 token 匹配时续期
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
          return redis.call('expire', KEYS[1], ARGV[2])
        else
          return 0
        end
        """
        return bool(self.client.eval(script, 1, self.key, self.token, self.ttl))

    def release(self) -> None:
        # Lua 原子化：仅 token 匹配时删除（防止误删别人的锁）
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
          return redis.call('del', KEYS[1])
        else
          return 0
        end
        """
        self.client.eval(script, 1, self.key, self.token)

    def keep_alive_loop(self) -> None:
        while True:
            time.sleep(self.ttl // 3)
            if not self.renew():
                # 续期失败 = 锁已被抢占 → 自杀，让 standby 接管
                logger.error("Leader lock lost, exiting scheduler process")
                os._exit(1)
```

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

### 4.9 WebSocket（保留现状，迁移代码位置）

- `web` 进程的 `lifespan` 启动 `redis_subscriber` 异步任务（Redis Pub/Sub → WebSocket 广播）
- WebSocket 路由从 `src/app/websocket.py` 迁移到 `src/controllers/system/websocket.py`（或保留独立位置）
- payload 不走 `Response[T]` envelope，直接推送事件结构

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
- 引入 `src/utils/{log,redis,time,uuid,trace_id,json,serializers}/`
- 引入 `src/middleware/{request_logging,error_logging}/`
- `src/app/app.py` 中间件栈注入 CorrelationId / RequestLogging / ErrorLogging（**响应/异常体系不变**）
- 现有 `src/shared/db.py` 改成转发 wrapper（指向 `src/db/session.py`），逐步废弃

**验收**：
- 所有现有测试全绿（53 通过）
- 启动 + 健康检查 OK
- HTTP 行为零变化（前端无感知）

**回滚**：单 PR，revert 即可

### 阶段 2：DB 层扁平化

**范围**：
- `shared/models/` → `src/models/`（一实体一文件，~17 个）；`__init__.py` 显式导入维护
- 引入 `src/cruds/base_crud.py` + 一实体一 crud（~17 个）
- `src/schemas/` 平铺迁移
- Alembic 配置迁移到 `src/db/alembic.ini`（migrations 目录视情况移动；如 schema 文件路径改动，走 `alembic revision`）
- service 层暂时保留旧调用方式（直接 `session.query(Model)`），但**新加方法必须走 cruds**

**验收**：
- 所有测试全绿
- **DB schema 必须零变化**：阶段 2 是纯代码搬迁，模型字段、约束、索引一律不动；如发现 schema diff 必须中止合并、单独走 `alembic revision` 在独立 PR 解决
- Alembic `alembic upgrade head` 在干净库上可以跑通；新旧路径切换后 `alembic current` 一致

**回滚**：单 PR，revert + 数据库不需要回滚（schema 未变）

### 阶段 3：业务层重组

**范围**：
- 现有 `src/{execution,insight,strategy,events,control,services,workers}/` 按 B-Hybrid 重组到 `src/services/{execution,insight,strategy,risk}/`
- 抽 `src/core/{exchange,llm,indicators,trace}/` 容纳无状态计算 / 外部客户端
- 现有 `src/workers/{strategy_loop,position_monitor,...}.py` 暂留，作为"调用 services/* 的薄壳"，不动 lifespan
- service 层全面切到 cruds 调用（不再裸 SQL）

**验收**：
- 所有测试全绿
- HTTP / WebSocket / scheduler 行为零变化

**回滚**：单 PR，revert 即可（仅文件搬移 + import 路径变更）

### 阶段 4：响应/异常体系切换

**范围**：
- `src/app/routers/*` → `src/controllers/api/v1/{domain}/*`
- 所有 controller 加 `@api_response()` 装饰器，返回 `Response[T]`
- 引入业务异常树（`BizError` 子类）；现有 `HTTPException(404,...)` 全替换为 `raise NotFoundError(...)`
- 注册全局 exception handler
- **前端 fetch 封装层同步升级**（解 `data` 字段、判 `code` 字段、处理 trace_id）
- 前端所有调用点 e2e 验证

**验收**：
- 所有后端测试全绿
- 前端单测 + e2e 跑通
- HTTP 响应格式按规范升级（手工测试覆盖关键接口：登录 / 持仓查询 / 平仓 / 决策列表 / 风控事件）

**回滚**：本阶段是真正的 breaking change，回滚需要前后端同时 revert；建议合并前在 dev 环境跑 24h 观察

### 阶段 5：scheduler 进程拆分 + APScheduler 持久化

**范围**：
- `scripts/start_web.py` + `scripts/start_scheduler.py` 创建
- `src/schedulers/{leader_lock,strategy_pipeline_scanner,position_monitor_scanner}.py` 创建
- APScheduler 切 `SQLAlchemyJobStore`（PostgreSQL `apscheduler_jobs` 表，通过 `alembic revision` 创建）
- `src/app/app.py` lifespan 移除 scheduler 启动逻辑（仅保留 WebSocket 订阅 + admin bootstrap）
- `docker-compose.{local,dev-server,test,prod}.yml` 增加 `scheduler` service
- `Makefile` 增加 `make dev-scheduler` 目标
- `scripts/deploy-dev.sh` 同步更新（拉镜像 + 启 web + 启 scheduler）
- 旧 `src/workers/*` 删除

**验收**：
- 所有测试全绿
- dev server 部署：web + scheduler 双进程同时运行，scheduler 重启后 job 状态从 `apscheduler_jobs` 表恢复
- 多 Pod 模拟（在 dev 上启 2 个 scheduler 容器）：仅 1 个 leader 跑 job，另一个 standby；leader 容器 kill 后 standby 30s 内接管

**回滚**：本阶段涉及部署形态，回滚需更新 docker-compose 回到单 service + lifespan 启动 scheduler；建议合并前充分测试

---

## 7. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 阶段 4 前端忘记升级，API 上线后前端报错 | 中 | 高 | 阶段 4 前后端同 PR 合并；dev 环境必须验证 e2e |
| Alembic 在阶段 2/5 自动生成迁移漏字段 | 中 | 高 | 每次 `alembic revision --autogenerate` 后必须人工 review；启用 `compare_type=True` |
| Scheduler leader 锁丢失（网络分区导致 Redis 不可达） | 低 | 中 | `keep_alive_loop` 续期失败时进程自杀（`os._exit(1)`），交给 Docker restart 重新参选 |
| APScheduler `SQLAlchemyJobStore` 与 alembic 自动生成冲突 | 低 | 中 | `apscheduler_jobs` 表不放在 SQLAlchemy `metadata` 内，`alembic env.py` 用 `include_object` 排除 |
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

## 10. 后续工作（不在本次重构内）

- 性能与可观测性章节落地（连接池监控、慢查询日志、应用层中间件计时）
- APScheduler `RedisJobStore` 实验（如 PG JobStore 出现锁竞争问题）
- 多策略并行架构（每个策略独立 pipeline + 独立持仓桶）
- 幂等 trace_id 升级到 Redis 缓存层（避免重复落库）

---

**文档结束**。请老板审阅；通过后将进入 `writing-plans` 流程产出实施计划。
