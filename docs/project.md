# AlphaPilot 工程规范（项目宪法）

> **本文档是 AlphaPilot 项目的工程"宪法"。任何编码工作开始前必须先读完本文档。**
>
> - 创建于：2026-05-01（Stage 1-5 重构完成）
> - 关联：[spec v3.7](superpowers/specs/2026-04-30-fastapi-template-refactor-design.md) / [模板原文](fastapi-project-template-v3.md)
> - 修改流程：必须 PR review；任何条款变更必须说明"为何变更"+"对存量代码的影响"

---

## 0. 阅读须知

### 适用范围
- 后端 Python 代码（`backend/src/`、`backend/tests/`、`backend/scripts/`）
- 前后端共享的 API 契约
- 数据库 schema 与 alembic 迁移

### 优先级
1. **用户/老板的明确指示**（CLAUDE.md / 直接消息）— 最高优先级
2. **本文档（项目宪法）**— 次之
3. **spec / 模板** — 设计参考，但被本文档覆盖时以本文档为准

### AI 协作必读
任何 AI 助手开始编码前必须读：
1. `CLAUDE.md` — 项目快速恢复指南
2. `docs/project.md`（本文档）— 工程宪法
3. `.claude/memory/MEMORY.md` — 会话记忆索引

---

## 1. 项目结构（B-Hybrid）

```
backend/
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── migrations/versions/        # 单初始 migration（Stage 2 重建后）
├── scripts/
│   ├── start_api.py            # API 进程入口（uvicorn 多 worker）
│   ├── start_scheduler.py      # scheduler 进程入口（APScheduler + EventShuttle + 任务队列）
│   ├── init_db.py
│   ├── upgrade_db.py
│   └── create_tables.py
├── src/
│   ├── app.py                  # FastAPI 应用工厂（提级到 src 根级，模板规范）
│   ├── configs/                # 8 个子配置类多继承
│   ├── common/                 # 通用 schema / 异常 / 响应 / 装饰器
│   │   ├── api_response.py
│   │   ├── events.py
│   │   ├── exception/
│   │   ├── response/
│   │   └── pagination.py        # Paginated[T] 泛型（顶层；Task 8）
│   ├── controllers/            # API 路由层（Stage 4 重组）
│   │   ├── dependencies.py
│   │   ├── rate_limit.py
│   │   ├── router.py           # 主聚合
│   │   ├── websocket.py
│   │   └── api/v1/             # 按领域分子目录
│   │       ├── execution/      # account / positions / trades
│   │       ├── strategy/       # decisions / reports
│   │       ├── risk/           # commands / risk_events
│   │       └── system/         # admin / auth / events_catchup / health / runtime_config
│   ├── core/                   # 无状态计算 / 外部客户端
│   │   ├── exchange/           # adapter / binance_adapter / binance_client / rate_limiter / retry / types
│   │   ├── llm/                # client（DeepSeek / OpenAI 兼容）
│   │   ├── indicators/         # （占位，未来 pandas-ta 算子）
│   │   └── trace/              # （占位，幂等 trace_id 生成）
│   ├── cruds/                  # 数据访问层（一实体一文件 + base_crud.py）
│   ├── db/                     # engine / session
│   ├── middleware/             # CorrelationId / RequestLogging / ErrorLogging
│   ├── models/                 # ORM models（一实体一文件 + base.py）
│   ├── schedulers/             # APScheduler scanner + EventShuttle daemon
│   ├── services/               # 业务编排层（B-Hybrid 按领域聚合）
│   │   ├── execution/          # 5 个 service + 5 个 _service.py
│   │   ├── insight/            # indicators_calculator / regime_classifier / experience_store + 子目录
│   │   ├── risk/               # kill_switch
│   │   ├── strategy/           # decision_engine / pipeline / proposal / router
│   │   ├── events/             # bus / contracts / inbox / outbox / ids
│   │   ├── manual_ops.py
│   │   ├── auth.py
│   │   └── admin_bootstrap.py
│   ├── shared/                 # 配置 / DB / enums 兼容 wrapper（阶段 6 渐废）
│   ├── utils/                  # log / request_id / uuid / time / redis / json
│   └── workers/                # 旧 worker（被 schedulers/ 调用，未来逐步合并）
└── tests/
    ├── conftest.py             # 测试库 alphapilot_test fixture
    ├── api/                    # router 集成测试
    ├── integration/            # 真 PG + Redis 集成
    └── unit/                   # 各模块单测
```

### 目录职责边界

| 目录 | 允许 | 禁止 |
|------|------|------|
| `src/controllers/` | HTTP 入参校验、路由、@api_response 装饰、调用 service | 写业务逻辑、直接访问 cruds、裸 SQL |
| `src/services/<domain>/` | 业务编排、调用 cruds + core | 直接 `session.query(Model)`、调用其它 controller |
| `src/cruds/` | 数据访问、SQL 表达 | 业务逻辑、跨表编排 |
| `src/core/` | 无状态计算、外部客户端封装 | DB 访问、业务规则 |
| `src/models/` | ORM 表定义 | 业务方法（应该在 service） |
| `src/common/` | 框架级工具（响应、异常、分页、事件 schema） | 业务代码 |
| `src/utils/` | 通用工具（无业务语义） | 业务代码 |
| `src/schedulers/` | APScheduler scanner、EventShuttle daemon | 业务逻辑 |

---

## 2. Python 环境与依赖

- **Python 3.12**（固定在 `backend/.python-version`，`pyproject.toml` `requires-python = ">=3.12"`）
- **venv 位置**：`backend/.venv/`（唯一）
- **包管理**：`uv`（路径 `D:\programs\uv\bin\uv.exe`）
- **重建 venv**：`cd backend && uv venv --seed --python 3.12 && uv sync`
- **新增依赖**：`cd backend && uv add <pkg>`（不要直接 pip install）
- **PYTHONPATH**：`backend/`（pytest `pythonpath = ["."]`，alembic `prepend_sys_path = .`）

### Import 规则（强制）

- **所有项目内部 import 一律 `src.` 开头**：
  - ✅ `from src.app import app`
  - ✅ `from src.models.position import Position`
  - ❌ `from app.app import app` / `from services.xxx` / `from shared.xxx`
- ASGI 入口：`src.app:app`（main.py / Makefile / docker entrypoint）

---

## 3. 配置体系

### 多继承聚合
`src/configs/app_configs.py` 按功能域拆 8 个子配置类，`AppConfig` 多继承聚合：

| 子配置类 | 字段 |
|---|---|
| ServiceConfig | ENVIRONMENT / LOG_LEVEL / UVICORN_WORKER_NUM / FASTAPI_ROOT_PATH |
| CORSConfig | ENABLE_CORS / CORS_ALLOWED_ORIGINS / CORS_EXPOSE_HEADERS |
| PostgreSQLConfig | PG_USER / PG_PASSWORD / PG_HOST / PG_PORT / PG_DB / POOL_SIZE / POOL_MAX_OVERFLOW / DB_CONNECT_TIMEOUT / PRINT_SQL |
| RedisConfig | REDIS_URL |
| SchedulerConfig | STRATEGY_LOOP_INTERVAL_MINUTES / POSITION_MONITOR_INTERVAL_SECONDS / APSCHEDULER_JOBS_TABLE / TASK_QUEUE_KEY / EVENT_BUS_CHANNEL / EVENT_SHUTTLE_BATCH_SIZE / EVENT_SHUTTLE_IDLE_SLEEP_SECONDS / EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS / SCHEDULER_GRACEFUL_SHUTDOWN_SECONDS |
| ExchangeConfig | TRADING_MODE / BINANCE_API_KEY / BINANCE_API_SECRET |
| LLMConfig | LLM_BASE_URL / LLM_API_KEY / LLM_MODEL / LLM_TIMEOUT_SECONDS |
| RiskConfig | MAX_POSITION_SIZE_PCT / MAX_DAILY_LOSS_PCT / MAX_CONSECUTIVE_LOSSES / MAX_SINGLE_RISK_PCT |
| SecurityConfig | APP_CONFIG_MASTER_KEY / APP_AUTH_SECRET_KEY / DEFAULT_ADMIN_* |

业务代码通过 `from src.configs import get_app_config` 访问，**禁止直接 import 子类**。

### `example.env` 同步规则
新增 / 删除 / 移动配置字段必须同步更新 `example.env`，字段顺序与子类列表严格一致。

### 环境变量黑白名单（CLAUDE.md 强制）
- ✅ Claude 可读写：`example.env`
- ❌ Claude 禁止访问：`.env`、`envs/*`、`backend/.env`、`frontend/.env.local`、任何子目录真实 env

---

## 4. 数据库规范

### 同步 SQLAlchemy（强制）
- HTTP API、scheduler、CRUD 全部使用 `sqlalchemy.orm.Session`（同步）
- **禁止** AsyncSession / `async def` 端点 / `await session.execute(...)`

### 主键约定
- **每个 model 文件第一字段必须是 `id`**：
  ```python
  id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  ```
- `Base` 不含 `id`（决策 2）
- 不再使用 `BigIntPk` sqlite variant（决策 3，已删）

### Base 通用字段（每表必有）
```python
class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="...")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="...")
    enable_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("TRUE"), comment="...")
    delete_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("FALSE"), comment="...")
```

### TradingModeMixin（按需继承）
- 业务表（Position / Order / Trade / Decision / Indicator / Regime / ...）继承 `TradingModeMixin`
- 全局表（User / SystemSetting / AuditLog / SymbolConfig）不继承

### 外键约束
- **CLAUDE.md 强制：禁止任何外键约束**
- 关联靠业务层 ID 维护
- 索引仍要建（`index=True`）

### Model Field 单行规则（强制）
所有 `Mapped[...] = mapped_column(...)` 字段定义**必须保持单行**，便于 grep / IDE 跳转：

```python
# ✅ 正确（单行）
symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="...")

# ❌ 错误（多行）
symbol: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    index=True,
    comment="...",
)
```

### Session 规范
- `expire_on_commit=False`（Stage 1 默认）
- service 层 `commit()` 之后**必须**显式 `refresh(row)` 再返回（避免 DetachedInstanceError）
- CRUD 层**不 commit**；commit 由 service 显式调用
- HTTP 路径用 `CurrentSession`（Annotated[Session, Depends(get_db)]）
- scheduler / 脚本用 `with get_db_session() as session:`

### Alembic 迁移（CLAUDE.md 强制）
- **不允许手写迁移**：必须 `alembic revision -m "..."`（必要时 `--autogenerate`）
- Claude 只编辑生成文件的 `upgrade()` / `downgrade()` 正文
- `apscheduler_jobs` 表由 `SQLAlchemyJobStore` 自动管理，alembic `env.py::include_object` 排除

---

## 5. 分层与命名规范（核心）

### 五层职责
```
Controller (controllers/api/v1/{domain}/)
   ↓ 调用
Service (services/{domain}/)
   ↓ 调用
CRUD (cruds/)
   ↓ 操作
Model (models/)
```

外加 **Core**（services 调用，无状态计算 / 外部客户端）。

### 文件命名
- Model: `<entity>.py`（snake_case，单数）
- CRUD: `<entity>_crud.py`，单例命名 `<entity>_crud`
- Service: 类 + 单例（`xxx_service`），单例小写 snake_case
- Controller: `controllers/api/v1/<domain>/<feature>.py`（按领域子目录）
- Schema: 在 `services/<domain>/` 内或 `src/schemas/`（Pydantic）

### Schema 命名（强制）
| 用途 | 后缀 | 示例 |
|------|------|------|
| 实体响应（GET 返回 / List 元素） | `xxxRead` | `PositionRead`, `OrderRead` |
| 创建入参（POST body） | `xxxCreate` | `OrderCreate`, `LoginCreate` |
| 更新入参（PATCH body） | `xxxUpdate` | `OrderUpdate` |
| 非实体操作结果 / 复合返回 | `xxxOut` | `LoginOut`, `TaskSubmitOut` |
| 复杂查询参数 | `xxxQuery` | `OrderListQuery` |
| 分页响应 | `Paginated[xxxRead]` | `Paginated[OrderRead]` |
| service 内部 dataclass | 业务名（无后缀） | `DecisionContext`, `GuardCheckResult` |

**禁用命名后缀**：`xxxVO`（Java 风）、`xxxDTO`（Java 风）、`xxxRes`（缩写违 PEP 20）、`xxxResponse`（与 `Response[T]` envelope 撞名）、`xxxSchema`（过于宽泛）。

### CRUD 方法命名约定（强制）
- `add(session, **kwargs)` / `bulk_add(session, items)`
- `get(session, id)` 不存在抛 `DBException(NOT_FOUND)`
- `get_or_none(session, id)` 不存在返 None
- `find_by_<field>(session, ...)` 按条件查询，返列表
- `update(session, id, **kwargs)`
- `delete(session, id)` 软删（要求 model 有 delete_flag）
- `hard_delete(session, id)`
- 状态变更：`mark_<status>(session, id, ...)` / `bulk_mark_<status>(session, status_in=[...])`
- 失败累加：`bump_failed_attempts(session, id, error: str)`

### Import 依赖方向规则
- ❌ controller A 不能 import controller B
- ❌ service A 不能 import 跨领域 service B（`services/strategy/` 不能 `from src.services.execution.order_executor import ...` 直接调，必须通过领域内编排）
- ✅ controller → service → cruds + core
- ✅ service → cruds、core、models、common（events、exception 等）

---

## 6. API 契约

### `Response[T]` 结构
```json
{
  "success": true,
  "code": "0",
  "message": "成功",
  "detailMessage": null,
  "data": { ... 实际业务数据 ... },
  "request_id": "abc123def456..."
}
```

### `@api_response` 装饰器（强制）
所有 controller 函数加 `@api_response()` 装饰器；返回值就是 `data` 字段内容：

```python
@router.get("/{id}", response_model=Response[PositionRead])
@api_response()
def get_position(id: int, session: CurrentSession) -> PositionRead:
    return position_crud.get(session, id)
```

### HTTP 状态码 vs 业务 code（强制）
- **HTTP 状态码**：传输层语义（404 路径不存在、401 未授权、5xx 真异常）
- **业务 code**：`code` 字段（业务码段位）
- 业务异常**统一 HTTP 200 + body `success: false`**
- 真传输异常 → HTTP 4xx/5xx + body envelope（FastAPI 默认）

### WebSocket payload
WebSocket 推送**不走** `Response[T]` envelope，直接推事件结构。

### 错误码段位
| 段位 | 用途 |
|------|------|
| `"0"` | 成功 |
| `"400xxx"` | 客户端错误（参数 / 认证 / 权限 / 找不到 / 限流 / 冲突） |
| `"500xxx"` | 服务端错误（系统 / 服务层 / DB / Redis） |
| `"600xxx"` | alpha-pilot 业务专属（KillSwitch / RiskRejected / IdempotencyConflict / ...） |

---

## 7. 异常处理

### 异常树（`src/common/exception/errors.py`）
```
AppBaseException
├── ServiceException（业务层默认）
│   ├── KillSwitchPausedException
│   ├── RiskRejectedException
│   ├── IdempotencyConflictException
│   ├── InsufficientBalanceException
│   ├── ExchangeApiException
│   └── LLMResponseInvalidException
├── DBException（CRUD 层）
├── ParamsException（参数错误，关 stack 避免日志膨胀）
└── RedisException
```

### 抛错位置规范
- CRUD 层（`get` 不存在）→ 抛 `DBException(error_code=ErrorCode.NOT_FOUND)`
- Service 层业务规则违反 → 抛 `ServiceException(...)` 或具体业务子类
- 参数非法 → 抛 `ParamsException("xxx 不能为空")`

### 强制规则
- **业务代码禁止就地** `class XxxError(Exception)`
- 需要新语义在 `errors.py` 增子类
- **抛出时自动记 ERROR 日志**（含调用栈、`request_id`、`exc_class`）
- **handler 不重复记日志**：`AppBaseException` 由 `_auto_log` 在抛出点已记，handler 只做 JSON 转换
- **重抛禁止双记**：`except DBException: raise` 不要再 `logger.exception()`；要补上下文用 `logger.error(..., extra={...})`，不要包新异常

### 关于 `ErrorCode.NOT_FOUND` 段位
`NOT_FOUND` 错误码是 `"400005"`（4xx 客户端段位），由 `DBException` 子类抛出 — **段位 4xx vs 异常类 DBException** 不冲突：段位表达"客户端可见的错误"，异常类表达"抛出位置的技术分层"。

---

## 8. 异步任务与定时任务

### 双进程模型
| 进程 | 入口 | 职责 |
|------|------|------|
| api | `scripts/start_api.py` | FastAPI HTTP + WebSocket（多 worker） |
| scheduler | `scripts/start_scheduler.py` | APScheduler 定时任务 + EventShuttle daemon + 异步任务消费 |

scheduler 单容器（`replicas: 1` / `stop_grace_period: 60s`）。

### 任务持久化三层
1. **PostgreSQL `task_requests` 表** — 任务状态权威（pending/running/done/failed/cancelled）
2. **WebSocket 推送** — 实时层（业务事件 outbox → Redis Pub/Sub → ws）
3. **HTTP 状态查询** — 兜底层（`GET /api/v1/tasks/{task_id}`）

### `task_requests` 状态机
```
pending → running → done
                 ↘ failed
                 ↘ cancelled
```

### 不自动重试原则（交易系统）
失败任务不自动重试。`recover_orphan_tasks` 启动时把 `running` 孤儿标 `failed`，要求人工 review。

### api 进程禁止启动 APScheduler
默认 `lifespan` 不内嵌 scheduler。开发调试可设 `ALPHAPILOT_API_EMBED_SCHEDULER=1` 强开。

### 4 类后台任务场景决策
| 场景 | 方案 |
|------|------|
| 请求级 fire-and-forget（写日志、发通知）| FastAPI `BackgroundTasks` |
| HTTP 触发的耗时业务（一键全平仓、生成报告）| 写 `task_requests` 表 + scheduler 扫表执行 |
| api 进程级轻量定时（WebSocket 心跳、连接清理）| `lifespan` 启动 `asyncio.create_task` |
| 必须准时触发的定时任务（策略循环、监控、日报）| 全部归 scheduler 进程 |

---

## 9. 业务专属规范（alpha-pilot 特有）

### 交易模式隔离（`trading_mode` 字段）
- 所有业务表必须有 `trading_mode` 字段（'testnet' / 'mainnet'）
- 业务查询必须 filter trading_mode
- testnet 与 mainnet 数据物理共存但语义完全隔离

### 幂等 trace_id（业务键）
- `Order.trace_id = SHA256(decision_id:symbol:action)`
- 类型 `String(64)`，**不是主键**，是业务唯一索引
- 与 HTTP 链路 `request_id`（32 字符 hex UUID）严格区分

### 风控不可被 LLM 覆盖
- `ExecutionGuardService` 在 LLM 决策后强制校验
- 失败抛 `RiskRejectedException`，不进入下单链路

### LLM 兜底（解析失败 → HOLD）
- LLM 响应解析失败、缺 `stop_loss`、非法 `action` → 统一 fallback 为 `HOLD`
- 不允许"宁错勿空"

### kill_switch 检查点（每个 service 入口必须检查）
- 策略循环、持仓监控、订单执行入口都必须 `KillSwitchService(db).is_paused()` 检查
- 持仓监控允许 paused 时跑（监控-only 模式）

### 决策与订单的 ID 关联
- `Decision.id` ← `Order.decision_id` ← `Position.decision_id` ← `Trade.decision_id`
- 所有 ID 是 `BigInteger`，关联靠业务层维护（无 FK）

---

## 10. 日志与可观测性

### Logger 命名约定
- `app.exception` — 异常自动日志
- `app.exception_handler` — 全局 handler
- `app` — 应用工厂、路由
- `middleware.{request,error}` — 中间件
- `scheduler.{strategy_pipeline,position_monitor,event_shuttle}` — scheduler 容器内
- 业务模块用 `__name__`：`src.services.execution.order_executor`

### request_id 注入
- HTTP 链路：`asgi-correlation-id` 中间件自动注入 32 字符 hex UUID
- scheduler 链路：无 request_id（日志显示 "-"）
- formatter 自动包含 `request_id` 字段

### 异常日志分级
- **INFO**：业务有意为之（KillSwitchPaused 等）
- **ERROR**（默认）：业务可预期失败 + 基础设施异常
- **未识别 Exception**：handler 兜底 ERROR + 完整 traceback

### 不打印敏感字段
- API key / token / 用户密码不进日志
- `request_id` 可打印（链路追踪用）

---

## 11. 测试规范

### 测试库
- 本地 PG（5442）的 `alphapilot_test` 数据库（自动建库 + alembic upgrade）
- 不使用 sqlite（决策 3 已删）
- 每测试结束自动 DELETE FROM 所有表 + lock_timeout=3s

### 测试结构
```
tests/
├── conftest.py             # 全局 fixture
├── unit/                   # 单测（按业务分子目录）
│   ├── utils/
│   ├── common/
│   ├── cruds/
│   ├── models/
│   ├── control/            # kill_switch 等
│   ├── events/
│   ├── execution/
│   ├── insight/
│   ├── strategy/
│   └── workers/
├── integration/            # 集成测试（真 PG + Redis）
└── api/                    # router 集成测试
```

### 测试命名
`test_<功能>_when_<条件>_then_<期望>` 或 `test_<功能>_<场景>`。

### 覆盖率
保持当前水平（≥ Stage 5 末期 463 passed）。

### `@pytest.mark.skip` 慎用
- CLAUDE.md 强制：**不要禁用测试，修复它们**
- 如必须 skip，必须加 reason 注明"原因 + 何时修复"

---

## 12. Git 与发布流程

### 分支命名
- 重构：`refactor/<topic>`
- 修复：`fix/<topic>`
- 新功能：`feat/<topic>`

### Commit Message
- **中文**为主（CLAUDE.md 强制）
- 类型前缀：`feat / fix / refactor / docs / test / chore`
- 范围：`feat(<scope>): ...`
- 末尾包含 `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`

### 自动 push（CLAUDE.md 强制）
每次完成实现块：
1. 运行测试 / build 验收
2. `git commit`
3. `git push` — **立即推送，无需询问**
4. 测试通过后自动 `bash scripts/deploy-dev.sh`

### worklog（CLAUDE.md 强制）
工程性推进过程同步写入 `docs/worklog/`，命名 `YYYYMMDD_HHMM_<主题>.md`。

### 阶段性 PR 拆分
- 大重构按"逐域 / 逐 Wave"拆 PR
- 每 PR 测试全绿才能合并
- 合并后 dev 部署 24h 观察（关键变更）

---

## 附录 A. 决策日志

### 不引入 funboost
- 单 Pod 单实例场景 funboost 是过度工程
- 自家 Redis List 队列 + APScheduler + PG JobStore 完全够用
- 详见 spec §1.3 / §4.8

### 选同步 SQLAlchemy Session
- 与模板一致
- 交易系统优先正确性而非 I/O 并发
- async 的 footgun（DetachedInstanceError、relationship 必须 selectinload）对金融系统是负资产

### B-Hybrid 目录布局
- DB 层（model/crud/schema）扁平 — Alembic 友好、BaseCrud 模式自然
- 业务层（service/controller）按领域聚合 — 业务架构自我文档化
- 详见 spec §3.1

### 主键 BigInteger autoincrement
- 现实早已使用（30/30 用 BigIntPk + 4 升级 Integer→BigInt）
- Stage 2 删 `BigIntPk` 别名，统一直接 `BigInteger`

### 测试切本地新库 alphapilot_test
- 不用 testcontainers（启停 5-10s 慢）
- 用本地 PG (5442) 上的新库（启动一次自动建库 + alembic upgrade）
- 每测试结束 DELETE FROM 所有表 + lock_timeout=3s

### `xxxRead/Create/Update/Out` 命名
- FastAPI 官方教程主推风格
- 与 RESTful 动词对齐（Read/Create/Update/Delete = SELECT/INSERT/UPDATE/DELETE）
- 避免与 ORM model 撞名

### 业务异常统一 HTTP 200
- HTTP 状态码留给传输层语义
- 业务 code 在 body 区分
- 前端按 `success` / `code` 分类处理

---

## 附录 B. AI 协作指南

### 每次任务开始前必读
1. `CLAUDE.md` — 项目快速恢复指南
2. `docs/project.md`（本文档）— 工程宪法
3. `.claude/memory/MEMORY.md` — 会话记忆索引

### 常见反模式

| 反模式 | 正确做法 |
|---|---|
| `class FooVO(BaseModel)` | `class FooRead(BaseModel)` |
| `from src.shared.models import X` | `from src.models.X import X` |
| service 直接 `session.query(Model)` | 通过 cruds：`xxx_crud.find_by_xxx(session, ...)` |
| controller 写业务逻辑 | 调 service 编排，仅做 schema 转换 |
| `raise HTTPException(status_code=404, ...)` | `raise DBException(error_code=ErrorCode.NOT_FOUND, ...)` |
| `class CustomError(Exception):` 就地定义 | 在 `src/common/exception/errors.py` 加子类 |
| 多行 `mapped_column(...)` | 单行 |
| 测试用 sqlite | 用本地 alphapilot_test PG 库 |
| api 进程内嵌 APScheduler | 由 scheduler 进程独占 |
| async session | 同步 Session |

### 提交 PR 流程
1. 改动后跑 `pytest -q` 确保 463+ passed
2. `git commit` 用中文 message + 类型前缀
3. `git push` 立即推送
4. 验收通过 `bash scripts/deploy-dev.sh` 部署 dev
5. 写 worklog 到 `docs/worklog/`

---

## 附录 C. 与 spec / 模板的差异说明

| 项 | 模板 v3 | alpha-pilot 现状 |
|---|---|---|
| 数据库 | MySQL 8.0 + pymysql/mysqlclient | PostgreSQL 16 + psycopg2-binary |
| 异步任务 | funboost + Redis Stream | APScheduler + Redis List + PG JobStore |
| 进程模型 | web + worker + scheduler 三进程（supervisor） | api + scheduler 双 service（docker-compose） |
| 测试 | sqlite in-memory + savepoint | 本地 PG `alphapilot_test` + DELETE FROM |
| 日志库 | nb_log | stdlib logging |
| JSON 序列化 | msgspec | stdlib JSON |
| Phoenix 追踪 | 可选 | 不引入 |
| 飞书 SDK | 默认 | 不引入 |

---

**End of project.md** — 本文档随 alpha-pilot 演化，关键变更必须 PR review。
