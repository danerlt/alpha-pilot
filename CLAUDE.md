# AlphaPilot — Claude 上下文恢复指南

本文件帮助 Claude（和开发者）在任意机器上快速恢复项目开发上下文。

## 快速恢复

在新机器上开启新的 Claude 会话时：

1. 克隆仓库并 `cd` 进入项目目录
2. 告诉 Claude：**"读取 CLAUDE.md、docs/project.md 和 .claude/memory/ 目录下所有记忆文件，然后继续开发"**
3. Claude 会读取 `.claude/memory/MEMORY.md` 及所有链接文件，恢复完整上下文

> **编码前必读优先级**：① 用户/老板明确指示 → ② [`docs/project.md`](docs/project.md)（工程宪法，全量结构/命名/分层/API 契约/异常/异步/日志/测试/Git 规范）→ ③ spec v3.7 / 模板。本 CLAUDE.md 仅为"快速恢复指南"，结构细节以 project.md 为权威。

---

## Python 环境规则（强制）

- **Python 版本：3.12**（固定在 `backend/.python-version`，`pyproject.toml` 中 `requires-python = ">=3.12"`）
- **venv 位置：`backend/.venv/`**，唯一虚拟环境，根目录不建 venv
- **包管理器：uv**，路径 `D:\programs\uv\bin\uv.exe`
- 重建 venv：`cd backend && uv venv --seed --python 3.12 && uv sync`
- 新增依赖：`cd backend && uv add <包名>`，不要直接用 pip install
- PyCharm 解释器路径：`E:/ai/alpha-pilot/backend/.venv/Scripts/python.exe`

---

## 后端 Python 包导入规则（强制）

- PYTHONPATH 根目录为 `backend/`（pytest `pythonpath = ["."]`，alembic `prepend_sys_path = ../..`，配置在 `src/db/alembic.ini`）
- **所有项目内部 import 一律以 `src.` 开头**，例如（v3.7 重构后 `app.py` 提级到 src 根，`shared/` 已拆解）：
  - ✅ `from src.app import app`
  - ✅ `from src.models.position import Position`
  - ✅ `from src.schemas.auth import LoginCreate` / `from src.core.trace.trace_id import generate_trace_id`
  - ❌ `from src.app.app import app` / `from src.shared.models.xxx import yyy` / `from services.xxx import zzz`
- ASGI 入口统一为 `src.app:app`（scripts/start_api.py / scripts/start.sh / Makefile / docker entrypoint）
- 第三方依赖通过 `uv sync --extra dev` 安装；新增依赖改 `backend/pyproject.toml` 后必须 `uv sync` 一遍并提交 `uv.lock`

---

## 项目简介

**AlphaPilot** — AI 自主数字货币现货交易系统，面向 Binance，V0.1 仅支持现货做多。

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, APScheduler |
| LLM | OpenAI 兼容协议（默认 DeepSeek，可配 base_url 切换任意端点） |
| 交易所 | Binance Testnet + Mainnet（python-binance） |
| 数据库 | PostgreSQL 16 |
| 缓存/事件总线/任务队列 | Redis 7（Pub/Sub + BRPOP 任务队列） |
| 认证 | JWT（python-jose）+ bcrypt（passlib），含管理后台 |
| 部署 | Docker Compose |

---

## 当前实现状态（截至 2026-05-02）

> ⚠️ 旧的 Phase 1/2/3 阶段划分已被 2026-04~05 的 **FastAPI 模板全量重构（spec v3.7）** 取代。当前以"重构 + 规格收口"为主线，工程宪法见 [`docs/project.md`](docs/project.md)。

| 里程碑 | 内容 | 状态 |
|------|------|------|
| 原型 Phase 1-3 | DB 模型、核心服务、Worker、REST API、WebSocket、Next.js 前端 | ✅ 完成 |
| v3.7 重构 Stage 1-5 | 迁到分层模板：`controllers/services/cruds/schemas/models/core/db`，alembic 重建 | ✅ 完成 |
| 认证 + 管理后台 | JWT 登录注册、`admin_bootstrap`、用户/审计日志/币种管理（前后端） | ✅ 完成 |
| 异步任务调度（§4.9.1） | `task_dispatcher` + Redis BRPOP + 孤儿恢复 + `task_request` 状态机 | ✅ 已闭环（close-all 已切异步入队 + `GET /api/tasks/{id}` 兜底 + `task.status_changed` 实时事件） |
| Spec Gap Closure | 11 个差距项全清，**100% 对齐 spec v3.7** | ✅ 完成 |
| Windows 全流程差距收口 | OPS/前后端/文档 差距审计后逐项实现（见 worklog 2026-06-13） | ✅ 完成 |

**测试基线：453 passed + 2 skipped（全绿）。前端 `next build` + `tsc --noEmit` 通过。**

---

## 已实现功能

### 后端服务（`backend/src/services/`，已按域拆子目录：strategy/risk/execution/insight/reporting/events/system）

> 下表为业务能力概览；权威目录布局与命名规范见 [`docs/project.md`](docs/project.md) §1。

| 服务 | 功能 |
|------|------|
| market_data | Binance K线拉取 + DB UPSERT（自动切换 testnet/mainnet） |
| account_state | 账户余额/PnL 快照同步 |
| indicators | EMA20/50/200, RSI(14), MACD(12,26,9), ATR(14), 布林带(20), 成交量MA, 波动率 |
| regime | 市场状态识别：trending_up / trending_down / ranging / chaotic |
| decision_engine | LLM Prompt 构建 + JSON 解析（失败兜底 HOLD）+ Claude/OpenAI 调用 |
| execution_guard | 风控校验 PASS/REJECT/DEGRADE（日亏损熔断、连续亏损、仓位上限、单笔风险） |
| order_execution | 幂等开多/平多（trace_id = SHA256(decision_id:symbol:action)），写 Position+Order+Trade |
| monitoring | 止损检测、止盈轮询、日亏损熔断触发 |
| experience_store | 已平仓交易经验记录与检索（含 experience_v2） |
| reporting | 每日日报生成 |
| auth / admin_bootstrap | JWT 登录注册、首次管理员引导、审计日志 |
| task_dispatcher | Redis BRPOP 任务消费 + 状态机流转 + 孤儿任务恢复（§4.9.1） |
| event_bus / ws_manager | 事件总线（Pub/Sub）+ WebSocket 连接管理 |

新增数据域（27 张表）：`event_store`（事件溯源）、`factor`、`shadow`、`attribution`、`ops_diagnosis`、`decision_review`、`agent_invocation`、`prompt`、`task_request`、`user`、`audit_log`、`symbol_config`、`system_setting` 等。

### 调度进程（`backend/src/schedulers/`，入口 `scripts/start_scheduler.py`）

| 调度器 | 触发频率 | 功能 |
|--------|----------|------|
| strategy_pipeline_scanner | 每 15 分钟 | 完整策略链：行情→指标→状态→决策→守卫→下单→发布事件 |
| position_monitor_scanner | 每 10 秒 | 止损检测 + 止盈轮询 + 熔断检查 |
| event_shuttle | 常驻 | 事件搬运（DB event_store ↔ Redis Pub/Sub） |

> 注：旧的 `src/workers/` 业务逻辑已重组进 `src/schedulers/` + 各 `services/` 子域。

### REST API（`/api/...`）

| 接口 | 功能 |
|------|------|
| `GET /api/positions` | 当前开仓持仓 |
| `POST /api/positions/{id}/close` | 手动平仓（绕过 AI） |
| `POST /api/positions/close-all` | 一键全部平仓（紧急操作） |
| `GET /api/trades` | 已平仓交易记录 |
| `GET /api/decisions` | AI 决策日志 |
| `GET /api/risk-events` | 风控事件日志 |
| `POST /api/risk-events/{id}/resolve` | 手动解除熔断 |
| `GET /api/reports` | 每日报告列表 |
| `POST /api/reports/generate` | 手动触发今日日报 |
| `GET /api/account` | 最新账户快照 |
| `POST /api/auth/login` `register` | JWT 登录 / 注册 |
| `/api/admin/...` | 管理后台：用户、审计日志、币种配置 |
| `/api/commands` | 命令/异步任务入口（接 task_dispatcher） |
| `/api/runtime-config` | 运行时配置读写 |
| `/api/events/catchup` | WebSocket 断线事件补偿 |
| `GET /api/health` | 健康检查 |

> 控制器层位于 `src/controllers/api/v1/{execution,risk,strategy,system}/`；前端页面：`/login` `/register` `/admin/{users,audit-logs,currencies}` + 实时 Dashboard。

---

## 关键设计决策

- 所有表含 `trading_mode` 字段（testnet/mainnet 数据完全隔离）
- 下单幂等性：`trace_id = SHA256(decision_id:symbol:action)`，重启可复现
- LLM 兜底规则：JSON 解析失败 / 缺失 stop_loss / 非法动作 → 统一回退 `HOLD`
- 熔断规则：日亏损 > 3% 或连续亏损 ≥ 3 笔 → 自动 REJECT，不可被 LLM 覆盖
- CHAOTIC 市场状态 → DEGRADE：OPEN_LONG 降级为 HOLD

---

## 开发命令

```bash
make deps-up        # 启动本机依赖栈：PostgreSQL(5442) + Redis(6389)（pytest / dev-backend 前置）
make dev-backend    # 启动 FastAPI 开发服务器（热重载，uv run 跨平台）
make init-db        # 初始化 Alembic 迁移（首次执行）
make upgrade-db     # 运行数据库迁移
make test           # 运行所有测试
make test-unit      # 仅运行单元测试
make test-integration # 集成测试（真 PG + Redis，依赖 make deps-up）
make lint           # ruff 检查
make fmt            # ruff 格式化
# 注：make dev-up/local-up 是整栈 docker（含前后端镜像），本机跑测试只需 make deps-up
```

> 全新克隆的环境需先初始化：后端 `cd backend && uv venv --seed --python 3.12 && uv sync --extra dev`；前端 `cd frontend && npm install`（会从 npmmirror 拉依赖并生成本地 lock）。
> 测试/本地后端依赖 PG(5442)+Redis(6389)，先 `make deps-up`（或 `docker start alpha-pilot-postgres-1 alpha-pilot-redis-1`）。

---

## 环境变量访问规则（全局强制）

文件布局：

```
alpha-pilot/
├── example.env       # ✅ 唯一模板, Claude 可读写, 提交 git
├── .env              # ❌ 老板专属, 不提交, 应用默认入口 (dotenv)
└── envs/             # ❌ 老板专属本地存档目录, 整目录 gitignore
    ├── local.env     #    本机开发
    ├── dev.env       #    远程 dev 服务器
    ├── test.env      #    自动化测试 / CI
    └── prod.env      #    生产
```

**白名单（Claude 可读写）：**
- `example.env`

**黑名单（任何工具——Read / Grep / Bash cat / Glob——一律禁止访问）：**
- 项目根 `.env`
- `envs/` 整个目录及其下所有文件
- 任何子目录的真实 env（`backend/.env`、`frontend/.env.local`、`*.env` 但 `example.env` 除外）

**配置变更工作流：**
1. Claude 改字段 → 只动 `example.env` 和代码默认值
2. 老板 review diff → 手动同步到 `envs/<env>.env` 与根 `.env`
3. 怀疑某真实值导致 bug → 老板手动 paste 相关行，Claude 不主动读

**部署加载方式：**
- Makefile / `scripts/deploy-*.sh` 通过 `--env-file envs/<env>.env` 加载
- docker-compose.{local,dev-server,test,prod}.yml 的 `env_file` 已指向 `../envs/<env>.env`
- 直接 `python` 跑应用时，dotenv 读项目根 `.env`（老板从 envs/ 拷贝过去）

## 环境变量配置

从 `example.env` 拷贝到 `envs/<env>.env` 填写后，再 `cp envs/<env>.env .env`：

```env
TRADING_MODE=testnet
BINANCE_API_KEY=<testnet key>
BINANCE_API_SECRET=<testnet secret>
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=<your llm api key>
LLM_MODEL=deepseek-v4-pro
DATABASE_URL=postgresql://alphapilot:alphapilot@localhost:5442/alphapilot
REDIS_URL=redis://localhost:6389/0
MAX_POSITION_SIZE_PCT=0.20
MAX_DAILY_LOSS_PCT=0.03
MAX_CONSECUTIVE_LOSSES=3
MAX_SINGLE_RISK_PCT=0.01
# 安全密钥（非测试环境启动必填，否则 _validate_secrets 抛 InsecureSecretError）
# 测试可设 ALPHAPILOT_SKIP_SECRET_VALIDATION=1 跳过；生产用 `python -c "import secrets;print(secrets.token_urlsafe(48))"` 生成
APP_AUTH_SECRET_KEY=<JWT 签名密钥，随机长串>
APP_CONFIG_MASTER_KEY=<Fernet 主密钥，runtime config 加密用>
# 开发/测试可选：自动引导默认管理员（生产勿用固定密码）
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=<强密码>
```

---

## 下一步（v3.7 收口后剩余）

1. ~~打通 controller → 异步任务真实路径~~ ✅ 已完成（close-all 切异步入队 + `GET /api/tasks/{id}` + `task.status_changed` 事件）
2. **dev 环境 24h 观察**：需老板亲自验证策略链/熔断/调度长时间稳定性
3. **持续回归测试**：当前 **453 passed + 2 skipped**，后续优先补前后端联调与更强的执行链路验证
4. **维护 alembic 迁移链**：配置已迁入 `src/db/alembic.ini`，后续 schema 变更统一走 migration（调用需带 `-c src/db/alembic.ini`）
5. **架构总览**：系统四平面划分/数据流/演进路线见 [`docs/总体架构.md`](docs/总体架构.md)

---

## 分支模型与 CI/CD（三环境）

> 详见 [`docs/deploy-ci.md`](docs/deploy-ci.md)。

```
feat-xxx ──PR──► dev ──PR──► uat ──PR──► main
                 │           │           │
              自动部署 dev  自动部署 uat  部署 prod(审批门)
              /ap-dev       /ap-uat       /ap
```

- `dev` / `uat` / `main` 三条长存分支，均从 `main` 切出；日常代码在 `feat-xxx`（从 dev 切）或 `dev`，**先合 dev**。
- push 到 `dev`/`uat`/`main` 由 GitHub Actions（`.github/workflows/deploy-{dev,uat,prod}.yml`）SSH 进服务器自动跑 `scripts/deploy-{dev,uat,prod}.sh`。
- prod 走 GitHub Environment 审批门（接 Binance mainnet，需人工 Approve）。

## 自动提交 & 推送规则

**每次完成一个实现块后，必须依次执行：**

1. 运行相关测试 / build 验收
2. `git commit` — 提交代码
3. `git push` — **立即推送到远程，无需询问用户**
4. push 到对应环境分支后，CI 自动部署（无需手动执行 deploy 脚本）

这确保代码在远程始终最新，换机器后直接 `git pull` 即可继续开发。

---

## 工程过程记录

- 除了 git 历史，自动执行的工程性推进过程也要同步写入 `docs/worklog/` 目录
- 建议按日期/主题拆分文件，例如：`docs/worklog/20260317_0822_第三阶段收尾.md`
- 适用范围：测试修复、迁移收口、部署一致性、文档对齐、低风险控制台改进
- 记录格式建议包含：做了什么、为什么做、如何验证、对应 commit

## 记忆文件

Claude 项目记忆存储在 `.claude/memory/`（已提交到 git）：

- `MEMORY.md` — 记忆索引（顶部链 `docs/project.md` 工程宪法）
- `project_alphapilot.md` — 项目架构和全局概览
- `project_phase2_services.md` — 早期实现进度追踪（历史）
- `feedback_auto_push.md` — 自动 push 规则
- `feedback_no_coauthor.md` — commit 不加 Co-Authored-By 行

> 工程性推进过程同步写入 `docs/worklog/`（最近主线：`20260502_0010_spec_gap_closure_全完成.md`）。

新会话开始时，让 Claude 读取这些文件即可恢复完整上下文。
