<div align="center">

<img src="AlphaPilot%20Design%20System/assets/logo_app.png" alt="AlphaPilot Logo" width="120" />

# AlphaPilot

**面向数字货币市场的 AI 自主交易系统 · Pilot your alpha.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Tests](https://img.shields.io/badge/tests-697%20passed-brightgreen)

</div>

---

AlphaPilot 是一个面向 **Binance** 的 **AI 自主数字货币现货交易系统**。
它的目标不是只做行情分析或信号提示，而是在 **严格风控** 和 **受限策略框架** 下，完成从市场理解、交易决策、自动执行到持续优化的完整闭环。

核心理念：**让 AI 不只是"建议交易"，而是在明确边界内真正参与交易，并通过经验积累持续提升。**

- AI 负责提出交易动作（`OPEN_LONG` / `CLOSE_LONG` / `HOLD`）
- 风控守卫负责决定是否允许执行（PASS / REJECT / DEGRADE，硬规则不可被 LLM 覆盖）
- 交易所只接受经过批准的指令，每一笔都可解释、可审计、可回放

---

## 界面预览

> 以下截图来自本机**真实全栈**（api + scheduler + webapp 三进程、真连 Binance testnet 行情）的浏览器验收实录，完整 15 步走查见 [docs/verification/本地浏览器验收_20260706.md](docs/verification/本地浏览器验收_20260706.md)。

### 主控台 Cockpit

AI 决策卡实时点亮五阶段（采集快照 → AI 推理 → 守卫检查 → 风险裁决 → 执行下单），权益曲线 + 右侧事件流 LIVE 滚动（调度器 → EventShuttle → Redis Pub/Sub → WebSocket 广播）。

![主控台](docs/verification/img/02_dashboard.png)

### 行情与手动下单

真实 K 线（含 TP/入场标线）、AI 市场解读（regime 判定 + 资金费率/持仓量/结算倒计时），右侧手动下单面板带**守卫预检逐项返回**——人工单同样受 10 项硬风控约束。

![行情页](docs/verification/img/04_market.png)

### 熔断全局联动（HALTED）

触发 KillSwitch 后五件套联动：顶栏胶囊变红「已熔断」、全局红色横幅、决策卡守卫 REJECT / 回退 HOLD、权益曲线变色、事件流置顶熔断红条。

![HALTED 联动](docs/verification/img/14_halted.png)

### 更多页面

| AI 决策流 | 策略实验室 |
|---|---|
| ![决策流](docs/verification/img/05_decisions.png) | ![实验室](docs/verification/img/09_lab.png) |
| PASS / REJECT / DEGRADE 三种守卫裁决徽章 + 推理全文 | 受控进化流水线 + SHADOW 候选（影子对比、promote 门槛） |

| 回测与绩效 | 后台管理 |
|---|---|
| ![绩效](docs/verification/img/07_performance.png) | ![后台](docs/verification/img/12_admin.png) |
| 胜率/盈亏比磁贴、vs HODL 曲线、月度 PnL、交易归因 | 用户管理 / 四角色权限矩阵 / 管理日志 |

完整 11 页：主控台 · 行情 · AI 决策 · 持仓与订单 · 回测与绩效 · 策略与风控 · 策略实验室 · 审计日志 · 后台管理 · 设置 · 登录，另有顶栏 Pilot AI 对话抽屉（SSE 流式）。

---

## 核心特性

### 1. AI 结构化交易决策

基于行情、技术指标（EMA/RSI/MACD/ATR/布林带）、账户状态和市场状态（Regime），LLM 输出结构化决策而非自由文本：

```json
{
  "symbol": "BTCUSDT",
  "action": "OPEN_LONG",
  "confidence": 0.78,
  "entry_price": 68250,
  "stop_loss": 67380,
  "take_profit": 69800,
  "position_size_pct": 0.12,
  "strategy_mode": "trend_following",
  "reasoning": ["1h趋势向上", "价格站上EMA20和EMA50", "MACD金叉"]
}
```

JSON 解析失败 / 缺失止损 / 非法动作 → 统一兜底 `HOLD`，绝不误下单。

### 2. 风控高于模型

所有决策（含人工手动单）必须通过执行守卫的硬校验：日亏损熔断（>3%）、连续亏损熔断（≥3 笔）、仓位上限、单笔风险、止损必填、风险收益比、CHAOTIC 市场降级等。**熔断规则不可被 LLM 覆盖。**

### 3. 自动执行闭环

行情拉取 → 指标计算 → Regime 识别 → LLM 决策 → 守卫裁决 → 幂等下单（`trace_id = SHA256(decision_id:symbol:action)`，重启可复现）→ 止损/止盈监控 → 事件溯源与实时推送，全链路无人值守。

### 4. 可解释、可审计

事件溯源（event_store 27 张表数据域）、AI 决策日志全文、风控事件、审计日志、每日复盘报告、逐笔交易归因（中文叙述 + 按币种/退出类型/regime/时段聚合拆解盈亏）。

### 5. 受控自我进化

策略评分器（策略×币种×regime 胜率/夏普/回撤）+ 影子模式（Shadow）验证 + promote 门槛，学习先验证再上线、可审计、可回滚。风险边界（最大仓位/日亏损上限/熔断规则）**永远不在自我修改范围内**。

---

## 系统架构

```
┌─────────────────────────── webapp (Vite SPA) ───────────────────────────┐
│  React 18 + TS strict + Tailwind(--ap-* token) + TanStack Query         │
│  OpenAPI 生成类型 · 单条 WS → zod 校验 → patch Query 缓存 · MSW mock    │
└──────────────┬───────────────────────────────┬──────────────────────────┘
               │ REST /api（JWT httpOnly cookie）│ WS /ws（EventEnvelope）
┌──────────────▼───────────────────────────────▼──────────────────────────┐
│  FastAPI (src.app:app)   controllers → services → cruds → models        │
│  按域拆分：strategy / risk / execution / insight / reporting / events   │
└──────┬───────────────────────────────────────────────────────┬──────────┘
       │                                                       │
┌──────▼──────────── scheduler 进程 ────────────┐   ┌──────────▼──────────┐
│ strategy_pipeline（15m 完整策略链）           │   │ PostgreSQL 16       │
│ position_monitor（10s 止损/止盈/熔断）        │   │ Redis 7             │
│ strategy_scoring / attribution（24h）         │   │ （Pub/Sub + BRPOP   │
│ event_shuttle（事件搬运 + notifier 告警）     │   │   任务队列）        │
└───────────────────────────────────────────────┘   └─────────────────────┘
                          │
                  Binance Testnet / Mainnet（trading_mode 数据完全隔离）
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy 2.x · Alembic · APScheduler · uv |
| 前端 | Vite · React 18 · TypeScript strict · Tailwind CSS · TanStack Query · lightweight-charts · MSW |
| LLM | OpenAI 兼容协议（默认 DeepSeek，可配 base_url 切任意端点；缺 Key 自动回退 Mock 恒 HOLD） |
| 交易所 | Binance Testnet + Mainnet（python-binance） |
| 数据库 | PostgreSQL 16（27 张表，全表带 `trading_mode` 隔离） |
| 缓存/事件/队列 | Redis 7（Pub/Sub 事件总线 + BRPOP 异步任务队列） |
| 认证 | JWT（httpOnly cookie + Bearer 双通道）+ bcrypt · 四角色权限矩阵 · 管理后台 |
| 设计系统 | `AlphaPilot Design System/`（`--ap-*` design token、组件预览、handoff 交付包） |
| 部署 | Docker Compose · nginx · GitHub Actions（build once, deploy many） |

> 配置分层：env 只放基础设施（PG/Redis/安全主密钥）；交易所 API Key 与 LLM 配置走前端设置页，Fernet 加密存库，DB 值优先于 env。

---

## 快速开始

```bash
# 1. 依赖栈（PostgreSQL 5442 + Redis 6389）
make deps-up

# 2. 后端环境（Python 3.12 + uv）
cd backend && uv venv --seed --python 3.12 && uv sync --extra dev && cd ..

# 3. 环境变量：从模板拷贝并填写（详见 example.env 内注释）
cp example.env .env

# 4. 数据库迁移
make upgrade-db

# 5. 启动
make dev-backend                                # FastAPI 开发服务器（热重载）
cd backend && uv run python scripts/start_scheduler.py   # 调度进程（另开终端）
cd webapp && npm install && npm run dev         # 前端（mock 模式；npm run dev:real 接真后端）
```

```bash
# 质量命令
make test               # 全部测试（697 passed + 2 skipped）
make lint / make fmt    # ruff 检查 / 格式化
make hooks              # 启用 pre-commit 钩子（提交前自动跑单元测试）
```

更多细节见 [docs/本地启动指南.md](docs/本地启动指南.md)。

---

## 项目结构

```text
alpha-pilot/
├── backend/                    # FastAPI 后端（spec v3.7 分层模板）
│   ├── src/
│   │   ├── app.py              # ASGI 入口 src.app:app
│   │   ├── controllers/api/v1/ # execution / risk / strategy / system
│   │   ├── services/           # 按域拆分：strategy/risk/execution/insight/...
│   │   ├── schedulers/         # 策略链 / 持仓监控 / 评分 / 归因 / 事件搬运
│   │   ├── cruds/ models/ schemas/ core/ db/
│   │   └── ...
│   ├── scripts/                # start_api / start_scheduler / export_openapi
│   └── tests/                  # unit + integration（真 PG + Redis）
├── webapp/                     # Vite SPA 前端主线（11 页 + 实时层）
├── frontend/                   # Next.js 旧前端（已冻结退役）
├── AlphaPilot Design System/   # 设计系统：token / 组件预览 / handoff 交付包
├── docker/                     # compose（local/dev/test/prod）+ nginx
├── scripts/                    # 三环境部署脚本
└── docs/                       # 工程宪法 project.md / 架构 / 验收 / worklog
```

---

## 分支模型与 CI/CD

```
feat-xxx ──PR──► dev ──PR──► uat ──PR──► main
                 │           │           │
              自动部署 dev  自动部署 uat  部署 prod（审批门）
```

push 到 `dev` / `uat` / `main` 由 GitHub Actions 自动 SSH 部署对应环境；prod 走 GitHub Environment 人工审批门（接 Binance mainnet）。详见 [docs/deploy-ci.md](docs/deploy-ci.md)。

---

## 当前状态

- ✅ 后端核心交易闭环 + 调度 + 事件溯源 + 异步任务（Redis BRPOP 状态机）
- ✅ 认证与管理后台（JWT + 四角色权限矩阵 + 审计日志）
- ✅ webapp 11 页全量落地并接真后端（OpenAPI 类型 + TanStack Query + WS 实时层）
- ✅ 通知系统 / 策略评分器 / 逐笔交易归因
- ✅ 测试基线 **697 passed + 2 skipped**，ruff 全仓 0 警告，e2e API 层 63/63 PASS
- ✅ 本机浏览器验收 15 步走查（本页截图即实录）
- ⏳ testnet 实盘验收（[验收手册](docs/testnet验收手册.md)已备）与 24h 稳定性观察

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/project.md](docs/project.md) | 工程宪法：结构/命名/分层/API 契约/异常/测试/Git 规范 |
| [docs/总体架构.md](docs/总体架构.md) | 系统四平面划分、数据流、演进路线 |
| [docs/webapp前端架构.md](docs/webapp前端架构.md) | 前端目标形态与前后端对接契约（已定稿） |
| [docs/产品需求文档.md](docs/产品需求文档.md) | 产品 PRD |
| [docs/本地启动指南.md](docs/本地启动指南.md) | 本地全栈启动步骤 |
| [docs/testnet验收手册.md](docs/testnet验收手册.md) | testnet 实盘验收清单 |
| [docs/verification/本地浏览器验收_20260706.md](docs/verification/本地浏览器验收_20260706.md) | 浏览器验收实录（17 张截图） |

---

## 一句话总结

**AlphaPilot 是一个面向 Binance 的 AI 自主数字货币交易系统，在严格风控和受限策略框架下，实现自动决策、自动执行与受控进化。**
