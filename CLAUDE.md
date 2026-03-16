# AlphaPilot — Claude 上下文恢复指南

本文件帮助 Claude（和开发者）在任意机器上快速恢复项目开发上下文。

## 快速恢复

在新机器上开启新的 Claude 会话时：

1. 克隆仓库并 `cd` 进入项目目录
2. 告诉 Claude：**"读取 CLAUDE.md 和 .claude/memory/ 目录下所有记忆文件，然后继续开发"**
3. Claude 会读取 `.claude/memory/MEMORY.md` 及所有链接文件，恢复完整上下文

---

## 项目简介

**AlphaPilot** — AI 自主数字货币现货交易系统，面向 Binance，V0.1 仅支持现货做多。

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, APScheduler |
| LLM | Claude claude-opus-4-6 / OpenAI（可配置） |
| 交易所 | Binance Testnet + Mainnet（python-binance） |
| 数据库 | PostgreSQL 16 |
| 缓存/事件总线 | Redis 7（含 Pub/Sub） |
| 部署 | Docker Compose |

---

## 当前实现状态

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | DB 模型（11张表）、FastAPI 骨架、Docker、Alembic | ✅ 完成 |
| Phase 2 | 全部核心服务 + APScheduler Worker + REST API | ✅ 完成 |
| Phase 3 | WebSocket Handler、Next.js 前端、数据库迁移、测试回归 | 🟡 已基本落地，进入收口阶段 |

---

## 已实现功能

### 后端服务（`backend/src/services/`）

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
| experience_store | 已平仓交易经验记录与检索 |
| reporting | 每日日报生成 |

### Worker（`backend/src/workers/`）

| Worker | 触发频率 | 功能 |
|--------|----------|------|
| strategy_loop.py | 每 15 分钟 | 完整策略链：行情→指标→状态→决策→守卫→下单→发布事件 |
| position_monitor.py | 每 10 秒 | 止损检测 + 止盈轮询 + 熔断检查 |

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
make dev-up         # 启动 Docker（PostgreSQL + Redis）
make dev-backend    # 启动 FastAPI 开发服务器（热重载）
make init-db        # 初始化 Alembic 迁移（首次执行）
make upgrade-db     # 运行数据库迁移
make test           # 运行所有测试
make test-unit      # 仅运行单元测试
```

---

## 环境变量配置

复制 `.env.example` 为 `.env` 并填写：

```env
TRADING_MODE=testnet
BINANCE_API_KEY=<testnet key>
BINANCE_API_SECRET=<testnet secret>
LLM_PROVIDER=claude
LLM_API_KEY=<anthropic api key>
LLM_MODEL=claude-opus-4-6
DATABASE_URL=postgresql://alphapilot:alphapilot@localhost:5442/alphapilot
REDIS_URL=redis://localhost:6389/0
MAX_POSITION_SIZE_PCT=0.20
MAX_DAILY_LOSS_PCT=0.03
MAX_CONSECUTIVE_LOSSES=3
MAX_SINGLE_RISK_PCT=0.01
```

---

## 下一步（Phase 3 收口）

1. **验证并维护数据库迁移链**：首个 Alembic 初始迁移已补齐，后续 schema 变更统一走 migration
2. **继续稳固 WebSocket/子路径部署**：重点关注 `/api` 与 `/ws` 在 dev/test/prod 下的一致性
3. **完善前端 Dashboard**：在现有实时面板基础上补空态/错误态、危险操作保护和环境提示
4. **持续回归测试**：当前 backend 测试已跑通（53 passed），后续优先补前后端联调与更强的执行链路验证

---

## 自动提交 & 推送规则

**每次完成一个实现块后，必须依次执行：**

1. `git commit` — 提交代码
2. `git push` — **立即推送到远程，无需询问用户**
3. Linux 服务器开发环境可用时，再执行 `bash scripts/deploy-dev.sh` 做自动部署

这确保代码在远程始终最新，换机器后直接 `git pull` 即可继续开发。

---

## 记忆文件

Claude 项目记忆存储在 `.claude/memory/`（已提交到 git）：

- `MEMORY.md` — 记忆索引
- `project_alphapilot.md` — 项目架构和全局概览
- `project_phase2_services.md` — 实现进度追踪
- `feedback_auto_push.md` — 自动 push 规则

新会话开始时，让 Claude 读取这些文件即可恢复完整上下文。
