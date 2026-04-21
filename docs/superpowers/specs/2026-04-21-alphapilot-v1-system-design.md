# AlphaPilot V1.0 系统设计文档（从零重新设计）

> 日期：2026-04-21
> 项目：AlphaPilot — 面向 Binance 的 AI 自主数字货币交易系统
> 范围：**V1.0 完整目标架构**（从零重新设计，现有代码与 2026-03-15 版仅作参考）
> 前置：
> - `docs/产品需求文档.md`（PRD v1，含 8.1 新采纳方向）
> - `AlphaPilot Design System/`（前端视觉与信息架构唯一真理）
> - 2026-03-15 旧版系统设计已归档为参考

---

## 目录

1. 设计总纲与核心决策
2. 系统分层与架构骨架（四平面）
3. 事件契约与数据流
4. Strategy Intelligence 平面内部结构
5. Factor & Insight 平面
6. Execution Core + 完整数据库 Schema
7. Control Plane + 前端（Design System 对齐）+ 消息端协同
8. 交付分期（V0.1 → V1.0）
9. 非功能要求
10. 开放问题

---

## 1. 设计总纲与核心决策

### 1.1 产品定位

AlphaPilot 是一个**在严格风控和受限策略框架下，实现 AI 自主决策、自动执行、交易复盘与受控进化的数字货币交易系统**。核心价值四词：**自主决策 · 风控约束 · 执行闭环 · 受控进化**。

### 1.2 本次设计的范围选择

按 PRD 和 3-17 新增方向确认，本次从零设计**目标架构 = PRD V1.0 全景**，分四个版本交付：

- **V0.1 MVP**：跑通自主交易闭环（现货做多 BTC/ETH）
- **V0.2**：归因 + Review AI + 消息端 + Program Trader
- **V0.3**：Shadow Mode + 学习控制器 + Ops AI
- **V1.0**：Factor AI + 完整多智能体闭环 + 合约（低杠杆）

### 1.3 核心架构决策

| # | 决策 | 选择 |
|---|------|------|
| 1 | 目标范围 | **V1.0 完整目标架构**（一次对齐全景，分版交付） |
| 2 | 用户与租户模型 | **单账户运行 + schema 全表预留 `account_id`**（多租户以后可开） |
| 3 | 决策层切分 | **混合：单进程多模块 + 明确事件契约**（四平面代码物理隔离、运行时可合一可拆开） |
| 4 | 循环触发模型 | **两段式：定时触发 Pipeline，Pipeline 内部同步，副作用走事件**（Redis Streams） |
| 5 | 智能体分工形态 | **一个 Worker 按序调用 Prompt→Decision→Review→Attribution，每步写审计表** |
| 6 | 前端视觉与信息架构 | **严格按 `AlphaPilot Design System/` 落地**（7 页主导航 + Web Shell） |
| 7 | 工程工作流 | 沿用 `CLAUDE.md`（每个实现块自动 `commit`→`push`→`deploy-dev`） |

### 1.4 不变的硬边界（PRD 9.5）

以下配置项标记为 `learnable=false`，**永远不接受学习控制器修改**：

- `MAX_POSITION_SIZE_PCT`
- `MAX_DAILY_LOSS_PCT`
- `MAX_CONSECUTIVE_LOSSES`
- `MAX_SINGLE_RISK_PCT`
- 熔断规则链
- "必须止损"规则
- "API 异常停机"规则

### 1.5 与旧实现的关系

| 维度 | 旧（2026-03 系统） | 新（本文档） |
|------|---------|---------|
| 代码组织 | `services/` 扁平 10 目录 | 按四平面分组 |
| 核心循环 | `strategy_loop.py` 290 行包一切 | Pipeline 编排 vs 具体能力分离 |
| 模块耦合 | 直接 import 业务函数 | 只依赖事件契约 dataclass |
| Factor 抽象 | 无（只有 indicators） | 独立因子层 + 因子定义表 |
| 决策路径 | 仅 AI | StrategyRouter 下挂 AI / Program / Shadow 三路 |
| 多智能体 | 仅一次 LLM 调用 | Prompt→Decision→Review（V0.1 规则，V0.2 LLM） |
| 归因 | 无 | V0.2 规则归因，V1.0 LLM 叙事 |
| 事件总线 | Redis Pub/Sub（不持久化） | Redis Streams（持久化 + 消费组 + 死信）+ Outbox |

**可复用**：指标计算算法、执行守卫核心规则、幂等 `trace_id`、Alembic 迁移基础、Fernet 密钥金库、前端认证与路由守卫、`AlphaPilot Design System/` 全部资产。

---

## 2. 系统分层与架构骨架

### 2.1 四个平面

AlphaPilot 按职责切成 4 个平面，**代码物理隔离、运行时可合一可拆开**：

```
┌─────────────────────────────────────────────────────────────┐
│  Control Plane（控制平面）                                  │
│  用户权限 / 审计日志 / 配置 / 启停开关 / 密钥 / 消息端路由 │
└────────────────────┬────────────────────────────────────────┘
                     │ 配置热更新 / 手动指令事件
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Strategy Intelligence Plane（策略智能平面）                │
│  AI Trader: Prompt AI → Decision AI → Review AI             │
│  Program Trader（V0.2+）/ Shadow Mode（V0.3+）              │
│  输出统一 DecisionProposal 事件                             │
└────────────────────┬────────────────────────────────────────┘
                     │ decision.proposed / reviewed
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Execution Core（执行核心）                                 │
│  Market Data / Account State / Execution Guard              │
│  Order Execution / Position Monitor                         │
│  输出 order.* / trade.* / position.* / risk.* 事件          │
└────────────────────┬────────────────────────────────────────┘
                     │ trade.closed / decision.* / risk.*
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Factor & Insight Plane（因子与洞察平面）                   │
│  Indicators / Factor Library / Regime Classifier            │
│  Attribution / Experience / Strategy Scorer / Reports       │
│  Ops & Diagnose AI（V0.3+）                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 运行时形态

- **MVP 部署**：单机 docker-compose：FastAPI 进程（含 APScheduler）+ PostgreSQL + Redis + Next.js
- **进程内部**：四平面各为独立 Python 包 + 独立 Worker/Service 类，**模块间只通过事件契约 + `RuntimeConfig` 通信**
- **演进路径**：任一平面可独立拆成进程/容器，只需替换 In-Process Event Bus → Redis Streams 适配器，不改业务代码

### 2.3 代码组织

```
backend/src/
├─ app/                          FastAPI 应用入口
│  ├─ app.py                     lifespan + 装配
│  └─ routers/                   按业务分组的 router（见 §7.2）
├─ control/                      Control Plane
│  ├─ auth/                      JWT + roles
│  ├─ account_config/            风控参数/币种
│  ├─ secret_vault/              Fernet 密钥
│  ├─ kill_switch/               停机/恢复/一键全平
│  ├─ manual_ops/                手动下单/平仓/解除熔断
│  ├─ audit_logger/              审计日志
│  └─ notifier/                  NotifyRouter（V0.2+）
├─ strategy/                     Strategy Intelligence Plane
│  ├─ router.py                  StrategyRouter
│  ├─ ai_trader/
│  │  ├─ pipeline.py
│  │  ├─ prompt_composer.py
│  │  ├─ decision_solver.py
│  │  ├─ review_critic.py
│  │  └─ llm_client.py           LLM Adapter
│  ├─ program_trader/            V0.2+
│  ├─ shadow/                    V0.3+
│  └─ learning_controller/       V0.3+
├─ execution/                    Execution Core
│  ├─ exchange/
│  │  ├─ adapter.py              ExchangeAdapter 接口
│  │  └─ binance_adapter.py
│  ├─ account_state/
│  ├─ guard/
│  ├─ orders/
│  └─ monitor/
├─ insight/                      Factor & Insight Plane
│  ├─ indicators/
│  ├─ factors/
│  │  ├─ registry.py
│  │  ├─ catalog/                6 个预置因子
│  │  └─ computer.py
│  ├─ regime/
│  ├─ experience/
│  ├─ attribution/               V0.2+
│  ├─ scorer/                    V0.2+
│  ├─ reporting/
│  └─ ops_ai/                    V0.3+
├─ events/                       事件总线
│  ├─ contracts.py               全部 dataclass 契约
│  ├─ bus.py                     In-Process 或 Redis Streams 适配
│  ├─ outbox.py                  Outbox 模式
│  └─ inbox.py                   消费幂等
├─ workers/
│  ├─ strategy_pipeline.py       15 分钟 Pipeline
│  ├─ position_monitor.py        10 秒持仓监控
│  └─ event_shuttle.py           Outbox → Streams 搬运
└─ shared/
   ├─ config.py
   ├─ runtime_config.py          Fernet 加密的运行时配置
   ├─ db.py
   ├─ enums.py
   └─ models/                    SQLAlchemy 模型
```

---

## 3. 事件契约与数据流

### 3.1 事件总线技术选型

- **主通道：Redis Streams**（持久化、消费组、可重放、支持死信）
- **实时推送：Redis Pub/Sub**（前端广播 / 消息端通知这类无需持久化的旁路）
- **进程内快路径**：Pipeline 同步段直接 Python dataclass 传参；Pipeline 结束写一次 `decision.cycle_completed` 到 Streams

### 3.2 事件契约公共头

所有事件包含：
- `event_id`（UUIDv7）
- `account_id`
- `trading_mode`
- `occurred_at`
- `trace_id`（关联同一 Pipeline 的所有事件）
- `schema_version`

### 3.3 事件目录（V1.0 全集，V0.1 只发布 ★ 事件）

| Stream | 事件 | 发布者 | 主要消费者 |
|--------|------|--------|-----------|
| `market.*` | `candle.closed` ★ | Market Data | Indicators, Factors |
| `factor.*` | `indicators.computed` ★ / `factors.updated` / `regime.classified` ★ | Factor Plane | Decision Pipeline, Attribution |
| `decision.*` | `proposal.drafted`（Prompt AI）/ `decision.proposed` ★ / `decision.reviewed` ★ / `decision.degraded` / `decision.rejected` ★ | Strategy + Guard | Shadow, Attribution, Notifier, WS |
| `order.*` | `order.submitted` ★ / `order.filled` ★ / `order.failed` ★ | Execution Core | Position, Notifier, WS |
| `position.*` | `position.opened` ★ / `position.updated` ★ / `position.closed` ★ | Execution Core | Experience, Attribution, Notifier |
| `trade.*` | `trade.closed` ★ | Execution Core | Experience, Attribution, Scorer, Report |
| `risk.*` | `risk.event.triggered` ★ / `circuit_breaker.*` ★ / `manual.override` | Guard / Ops | Notifier, WS, Audit |
| `learn.*` | `params.candidate.proposed` / `params.candidate.validated` / `params.applied` / `params.rolled_back` | Learning Controller | Audit, Notifier |
| `ops.*` | `ops.diagnosis` / `ops.heartbeat` | Ops AI | Notifier, Control Plane |
| `control.*` | `control.command.*`（停机/恢复/平仓/解熔断） | Control Plane | Execution Core |

### 3.4 策略循环 Pipeline 数据流

APScheduler 每 15 分钟触发（按 `account_id × symbol × timeframe`）：

```
[Trigger] StrategyCycleStarted (internal)
│
├─ 1. Market Data: fetch_candles()               → candle.closed ★
├─ 2. Factor Plane:
│       ├─ compute_indicators()                  → indicators.computed ★
│       ├─ compute_factors()                     → factors.updated
│       └─ classify_regime()                     → regime.classified ★
│
├─ 3. Pre-Check: circuit_breaker_active? yes → abort cycle
│
├─ 4. Strategy Plane（按 StrategyRouter 路由）:
│    ├─ path=AI_TRADER:
│    │    ├─ PromptComposer: build_prompt()      → proposal.drafted
│    │    ├─ ExperienceRetriever: retrieve_similar()
│    │    ├─ DecisionSolver: call_llm()          → decision.proposed ★
│    │    └─ ReviewCritic: validate+explain()    → decision.reviewed ★
│    └─ path=PROGRAM_TRADER (V0.2+):
│         └─ RuleEngine: evaluate()              → decision.proposed ★
│
├─ 5. ExecutionGuard: check(decision)
│       → PASS / REJECT → decision.rejected ★
│       → DEGRADE       → decision.degraded
│
├─ 6. Execution Core:
│       ├─ open_long / close_long (幂等 trace_id) → order.submitted ★
│       └─ sync_fill()                            → order.filled ★ + position.opened/closed ★
│
└─ [End] cycle.completed (internal; 写 audit_log)
```

**旁路消费者**（异步）：

```
decision.reviewed ─┬─► Shadow Runner（V0.3+）
                   ├─► Notifier（V0.2+）
                   └─► Attribution（V0.2+，等待 trade.closed 再归因）

trade.closed ─┬─► Experience Store
              ├─► Attribution AI → attribution.computed
              ├─► Strategy Scorer
              └─► Daily Report
```

### 3.5 持仓监控循环（独立，10 秒）

```
├─ update_prices()                    → position.updated ★
├─ check_stop_loss() 触发             → close_long → risk.event.triggered + trade.closed
├─ poll_take_profit() 触发            → trade.closed
└─ check_daily_loss() 触发            → circuit_breaker.triggered ★
```

### 3.6 幂等与错误处理

- **下单幂等**：`trace_id = SHA256(decision_id:symbol:action:sequence)`
- **事件消费幂等**：`event_inbox(consumer_name, event_id)` UNIQUE
- **Pipeline 内任一步异常** → `decision.rejected(reason=pipeline_error)`，不下单
- **事件消费失败** → Streams 消费组重试 3 次 → 死信 `deadletter.*` + 告警
- **Outbox 模式**：业务写 + 事件写在同一 DB 事务，后台 `event_shuttle` 搬到 Streams

---

## 4. Strategy Intelligence 平面内部结构

### 4.1 DecisionProposal 统一契约

所有策略路径的唯一对外产物：

```python
@dataclass
class DecisionProposal:
    account_id: int
    symbol: str
    timeframe: str
    action: Literal["OPEN_LONG", "CLOSE_LONG", "HOLD"]
    confidence: float
    entry_type: Literal["MARKET", "LIMIT"] | None
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    position_size_pct: float | None
    strategy_mode: Literal[
        "ai_trend", "ai_breakout", "ai_observation",
        "program_trend", "program_breakout",
    ]
    reasoning: list[str]
    risk_note: str | None
    # 元信息
    source: Literal["ai_trader", "program_trader", "shadow", "manual"]
    pipeline_version: str
    prompt_template_id: str | None
    llm_model_id: str | None
    factor_snapshot_id: int
    parent_proposal_id: int | None
    is_fallback: bool
```

Guard / Execution Core 只认此 schema。

### 4.2 AI Trader 路径（V0.1 主线）

```
AITraderPipeline.run(symbol, timeframe, context):
  ① PromptComposer
     输入: market/indicators/factors/regime/position/account/risk
     模板: 从 prompt_templates 表选 active 版本
     经验注入: ExperienceRetriever.top_k(symbol, regime)
     输出: PromptBundle(system, user, template_id, ctx_hash)
     持久化: proposal_drafts
  ② DecisionSolver
     调用 LLM (Claude/OpenAI/本地，可配置)
     强制结构化输出（JSON Schema + Pydantic 校验）
     失败路径 → 兜底 HOLD
     持久化: ai_decisions（含 prompt/response 原文）
  ③ ReviewCritic
     V0.1: 规则校验
     V0.2+: 规则 + LLM 二次审阅
     校验项:
       · SL/TP 在 ATR 合理范围
       · Risk/Reward ≥ min_rr_ratio
       · 与 regime 不冲突
       · 与最近 N 笔经验不矛盾
     输出: ReviewResult(approve/adjust/reject)
     持久化: decision_reviews
```

**LLM Adapter**：统一接口 `LLMClient.complete(system, user, schema) -> (parsed, raw, usage)`，Claude/OpenAI/本地可替换，不修改业务代码。

### 4.3 Program Trader 路径（V0.2+）

同一接口 `StrategyAdapter.propose(context) -> DecisionProposal`，实现为纯规则：

```
trend_following_v1:  EMA20>EMA50>EMA200 && MACD_hist>0 && volume>volume_MA → OPEN_LONG
breakout_v1:         price>bb_upper && volume>volume_MA*1.5 → OPEN_LONG
observation_v1:      regime=chaotic || volatility=low → HOLD
```

V0.1 只实装接口 + 占位 `observation_v1`，不路由到 Program 路径。

### 4.4 Shadow Mode（V0.3+）

订阅 `decision.reviewed`，用"候选参数版本"或"候选 Prompt 模板"再跑一次 Pipeline：

```
decision.reviewed → ShadowRunner
  ├─ 用 parameter_version 或 prompt_template 候选再跑
  ├─ 不调用 Execution Core
  └─ 写 shadow_decisions(source='shadow')

trade.closed → ShadowEvaluator
  对比当时真实决策 vs 影子决策的 PnL，写 shadow_evaluations
```

### 4.5 StrategyRouter

Pipeline 不直接调 AI/Program，走 Router：

```python
class StrategyRouter:
    def decide(self, ctx) -> DecisionProposal:
        # 1. 读 runtime_config 当前启用路径
        # 2. 按 symbol/regime/timeframe 决定路由
        # 3. 路由结果写 audit_log
```

V0.1 路由表仅一条：所有组合 → AI Trader。

### 4.6 多智能体实现（统一审计表）

| 智能体 | V0.1 形态 | V0.2+ 升级 |
|--------|-----------|-----------|
| Prompt AI | 规则拼 Prompt + 模板表 | LLM 按上下文重写 Prompt |
| Decision AI | LLM 调用 | 不变 |
| Review AI | 规则校验 | 二次 LLM 审阅 |
| Attribution AI | 规则归因 | LLM 叙事 |
| Ops AI | 不实装 | 异常检测 + 诊断叙事 |
| Factor AI | 不实装 | 候选因子发现 |

**所有智能体调用都落 `agent_invocations` 表**（统一：`agent_type / input_hash / prompt_template_id / model_id / tokens / latency_ms / output / outcome`）。

---

## 5. Factor & Insight 平面

### 5.1 指标 / 因子 / 特征 分层

| 层级 | 定义 | 示例 | 存储 |
|------|------|------|------|
| Indicator | 纯技术计算，无语义 | EMA20, RSI, MACD_hist, ATR | `indicator_snapshots` |
| Factor | 有语义信号，归一化到 [-1,1] | `trend_strength`, `breakout_validity` | `factor_snapshots` + `factor_definitions` |
| Feature | 决策时预处理向量/文本 | "EMA 多头 + 放量突破" | 内存，不落盘 |

**引入因子层的理由**：
- PRD 8.1.4 明确要求因子库 / 因子评估 / 因子触发 / 因子归因
- 指标是原始值，因子是结构化信号 → 提升可解释性和归因能力
- Program Trader 直接用因子表达规则，AI 与 Program 共享信号语言
- 归因引擎按因子维度分解盈亏

### 5.2 Factor 子系统

```
FactorEngine
├─ FactorRegistry（代码 + DB）
│  每个 Factor = Python 类 + factor_definitions 表记录
│  支持启用/停用/版本化
├─ FactorComputer
│  输入: indicators + 原始 K 线
│  对 active factor 调用 compute()
│  输出: FactorSnapshot
└─ FactorCatalog (V0.1 预置 6 个):
   · trend_strength       (多均线排列 + ADX)
   · momentum_quality     (MACD_hist + RSI 区间)
   · volume_confirmation  (当前量 vs volume_MA)
   · volatility_regime    (ATR 比率 + BB 宽度)
   · breakout_validity    (价格突破 + 量能 + 回踩)
   · pullback_opportunity (趋势 + 回撤深度)
```

V0.1 用规则计算；V0.3+ Factor AI 可提案新因子，写 `factor_candidates`，学习控制器验证后才能激活。

### 5.3 Regime Classifier（基于因子重写）

```
trending_up   ← trend_strength > 0.6  && volatility_regime != "high"
trending_down ← trend_strength < -0.6 && volatility_regime != "high"
ranging       ← |trend_strength| < 0.3 && volatility_regime = "low"
chaotic       ← volatility_regime = "high" || breakout_validity < 0
```

阈值存 `regime_thresholds`（可学习项，PRD 9.6）。

### 5.4 Attribution 引擎（V0.2+）

订阅 `trade.closed`，对每笔平仓结构化归因：

```python
@dataclass
class TradeAttribution:
    trade_id: int
    by_symbol: dict         # {"BTCUSDT": +0.8%}
    by_time_bucket: str     # "morning_asia" | "us_session"
    by_exit_reason: str     # "stop_loss" | "take_profit" | "ai_close" | "manual"
    by_factors: dict        # 决策时的因子快照
    factor_contributions: dict  # V0.3+ SHAP-like
    narrative: str | None       # V0.2+ LLM 生成
```

写 `trade_attributions` 表。

### 5.5 Strategy Scorer（V0.2+）

订阅 `trade.closed` + `trade_attributions`，按 `strategy_mode × symbol × regime × window(7d/30d)` 滚动计算：

```
strategy_scores: win_rate, pnl_sum, max_drawdown, sharpe,
                 false_breakout_rate, regime_fit_score, sample_count
```

评分低的策略 → 学习控制器降权或下线。

### 5.6 Experience Store（两级）

```
experiences（原始，每笔平仓一条）:
  id, trade_id, factor_snapshot_at_open, regime_at_open,
  strategy_mode, action_sequence, pnl_pct, hold_duration, exit_reason

experience_summaries（检索用，V0.2+）:
  id, summary_text,
  embedding(vector(1536)),  -- pgvector
  filter_tags
```

V0.1 只做 `experiences` + 标签检索；V0.2+ 引入 pgvector；V0.3 Attribution AI 生成 summary。

### 5.7 Learning Controller（V0.3+）

所有参数变更唯一入口（PRD 9.6 白名单）：

```
ParameterChangeProposal
  → Historical Validator（回放近 N 周历史）
  → Shadow Runner（N 天影子运行）
  → Gradual Rollout（小比例启用）
  → KPI 监控
     · 表现恶化 → 自动回滚（还原上一个 parameter_version）
     · 表现稳定 → 全量启用，写 parameter_versions
```

**硬风控（PRD 9.5）**标记 `learnable=false`，学习控制器直接拒绝修改。

### 5.8 Daily / Weekly Report

```
DailyReport:
  - 基础：胜率/PnL/最大单笔/最大回撤/决策次数/拒单次数
  - 市场：今日 regime 分布 + 因子均值
  - 归因（V0.2+）：因子 + 时段的盈亏分解
  - 风控事件清单
  - 典型案例：最大盈利 + 最大亏损各一笔的完整链路
  - 叙事（V0.2+）：Attribution AI 自然语言段落
  - 学习动作（V0.3+）：参数变更与回滚摘要
```

### 5.9 Ops & Diagnose AI（V0.3+）

订阅 `*.error / order.failed / risk.event.* / circuit_breaker.*`，先规则聚类再 LLM 生成诊断叙事，写 `ops_diagnoses`，推消息端。

---

## 6. Execution Core + 完整数据库 Schema

### 6.1 Execution Core 内部划分

```
ExchangeAdapter (Binance)
  - REST client + WS client
  - RateLimiter + 重试
  - testnet/mainnet 完全一致接口

AccountStateService
  - 余额/权益/持仓同步
  - account_snapshots

ExecutionGuard
  - 硬风控规则链 (不可被 AI 绕过)
  - PASS / REJECT / DEGRADE

OrderExecutor
  - open_long / close_long
  - trace_id 幂等
  - 部分成交处理

PositionMonitor
  - 止损秒级触发
  - 止盈轮询
  - 熔断检查
  - 位置价格刷新
```

### 6.2 ExchangeAdapter 改进点

- 所有调用经过 **RateLimiter**（令牌桶，Binance 权重 1200/min）
- 失败指数退避重试（≤3 次，单次超时 8s）；超限抛 `ExchangeTemporarilyUnavailable`
- Testnet/Mainnet 通过构造参数注入，**业务代码不再分支**
- WebSocket 行情订阅（V0.2+ 为 Program Trader 秒级路径准备）

### 6.3 ExecutionGuard 规则链（V0.1）

按顺序执行，一票否决：

1. 日亏损熔断 → REJECT
2. 连续亏损熔断 → REJECT
3. 账户可用余额不足 → REJECT
4. OPEN_LONG 且已有同币持仓 → REJECT
5. `position_size_pct > MAX_POSITION_SIZE_PCT` → REJECT
6. 单笔风险 > `MAX_SINGLE_RISK_PCT` → REJECT
7. SL 与当前价距离 < 0.5×ATR 或 > 5×ATR → REJECT
8. Risk/Reward < `min_rr_ratio` (默认 1.5) → REJECT
9. CHAOTIC regime + OPEN_LONG → DEGRADE → HOLD
10. Review AI `reject` → REJECT
11. PASS

每次 Guard 调用都落 `risk_events`（含 PASS 审计条）。

### 6.4 OrderExecutor 扩展

- `trace_id = SHA256(decision_id:symbol:action:sequence)`（支持部分成交重试）
- 下单后强制 `sync_order_fill()` 确认成交均价，再写 `positions`
- 支持部分平仓 `close_pct`（V0.1 仅全平，V0.2+ 开前端）
- 手动下单走同一接口 `OrderExecutor.open_long(payload, source='manual')`

### 6.5 手动操作守卫矩阵

| 操作 | 走 Guard | 跳过 |
|------|--------|------|
| AI 自动开仓 | ✅ 全链 | 无 |
| 手动开仓 | ✅ 大部分 | 跳过 Review AI 规则 |
| 手动平仓指定持仓 | ❌ | 全部 |
| 一键全平 | ❌ | 全部（紧急通道） |
| 手动触发熔断 | ❌ | 直接写 risk_events |
| 手动解除熔断 | ❌ | 直接更新 resolved |

所有手动操作必须写 `audit_logs`（含 `operator_user_id + reason`）。

### 6.6 完整数据库 Schema（V1.0）

所有业务表含 **`account_id`（多租户预留）** + **`trading_mode`（testnet/mainnet 隔离）** + `created_at` + `updated_at`。

#### 账户与配置类

```
accounts                 -- 单账户预留多租户
  id, owner_user_id, name, exchange, trading_mode,
  api_key_encrypted, api_secret_encrypted, enabled,
  risk_profile_id

users (现有，保留)
  id, username, email, password_hash, role, status, last_login_at

audit_logs (现有，扩展)
  id, account_id, user_id, action_type, resource,
  payload_json, reason, client_ip, occurred_at

system_settings (现有 runtime_config, Fernet 加密)
  key, value_encrypted, scope, updated_by, updated_at

risk_profiles
  id, account_id, name,
  max_position_size_pct, max_daily_loss_pct,         -- learnable=false
  max_consecutive_losses, max_single_risk_pct,       -- learnable=false
  min_rr_ratio, sl_atr_min_mult, sl_atr_max_mult,   -- 可调
  regime_thresholds_json,                            -- 可学习
  version, active

parameter_versions
  id, account_id, profile_id, change_type,
  old_value_json, new_value_json, reason,
  proposed_by_agent, validated_by, applied_at, rolled_back_at
```

#### 行情与因子类

```
symbols
  id, account_id, symbol, base_asset, quote_asset,
  enabled, priority, max_position_size_pct, timeframe, notes

candles
  id, account_id, trading_mode, symbol, timeframe,
  open_time, open, high, low, close, volume
  UNIQUE(trading_mode, symbol, timeframe, open_time)

indicator_snapshots
  id, account_id, trading_mode, symbol, timeframe, open_time,
  ema20/50/200, rsi, macd, macd_signal, macd_hist,
  atr, bb_upper/middle/lower, volume_ma, volatility

factor_definitions
  id, name, version, inputs_json, description,
  formula_code_ref, active

factor_snapshots
  id, account_id, trading_mode, symbol, timeframe, open_time,
  factors_json, factor_def_versions_json

regime_snapshots
  id, account_id, trading_mode, symbol, timeframe, open_time,
  regime, confidence, factor_snapshot_id

factor_candidates (V0.3+)
  id, proposed_by_agent, name, formula_code_ref,
  validation_status, validation_report_json, approved_at
```

#### 决策与执行类

```
prompt_templates
  id, name, version, system_template, user_template,
  variables_json, active, created_by

proposal_drafts
  id, account_id, trading_mode, symbol, timeframe,
  template_id, context_hash, rendered_system, rendered_user

ai_decisions (现有，扩展)
  id, account_id, trading_mode, symbol, timeframe,
  decided_at, action, confidence, entry_type,
  entry_price, stop_loss, take_profit, position_size_pct,
  strategy_mode, reasoning_json, risk_note,
  proposal_draft_id, prompt_input, raw_output,
  llm_provider, llm_model, tokens_used, latency_ms,
  is_fallback, source

decision_reviews
  id, decision_id, reviewer_type (rule/ai),
  result (approve/adjust/reject),
  adjustments_json, notes

risk_events (现有，扩展)
  id, account_id, trading_mode, event_type, symbol,
  triggered_at, description, position_id, decision_id,
  severity, resolved, resolved_by, resolved_at

orders
  id, account_id, trading_mode, symbol, side, order_type,
  quantity, price, binance_order_id, status,
  filled_quantity, avg_fill_price,
  trace_id (UNIQUE), decision_id, parent_order_id,
  submitted_at, filled_at, failed_reason

positions
  id, account_id, trading_mode, symbol, side,
  quantity, entry_price, current_price,
  stop_loss, take_profit,
  unrealized_pnl, unrealized_pnl_pct,
  opened_at, closed_at, status,
  opening_decision_id, opening_order_id

trades
  id, account_id, trading_mode, symbol,
  entry_price, exit_price, quantity, pnl, pnl_pct,
  hold_duration_sec, exit_reason, regime_at_open,
  opened_at, closed_at, position_id,
  opening_decision_id, closing_decision_id

account_snapshots
  id, account_id, trading_mode, snapshot_at,
  total_balance_usdt, available_balance_usdt,
  unrealized_pnl, daily_pnl, daily_pnl_pct
```

#### 智能体与学习类

```
agent_invocations
  id, account_id, agent_type, input_hash,
  prompt_template_id, llm_provider, llm_model,
  input_json, output_json, tokens_used, latency_ms,
  cost_usd, outcome, error, occurred_at

experiences
  id, account_id, trading_mode, trade_id, symbol, regime_at_open,
  strategy_mode, factor_snapshot_at_open_id,
  pnl_pct, hold_duration, exit_reason

experience_summaries (V0.2+)
  id, experience_id, summary_text,
  embedding vector(1536), tags_json, generated_by_agent

trade_attributions (V0.2+)
  id, trade_id, by_symbol, by_time_bucket, by_exit_reason,
  by_factors_json, factor_contributions_json,
  narrative, generated_at

strategy_scores (V0.2+)
  id, account_id, strategy_mode, symbol, regime,
  window, win_rate, pnl_sum, max_drawdown, sharpe,
  false_breakout_rate, regime_fit_score, sample_count

shadow_decisions (V0.3+)
  id, shadow_run_id, real_decision_id,
  proposal_json, parameter_version_id

shadow_evaluations (V0.3+)
  id, shadow_decision_id, real_trade_id,
  shadow_pnl_sim, real_pnl, diff

daily_reports (现有，扩展)
  id, account_id, trading_mode, report_date,
  summary_json, narrative_text

ops_diagnoses (V0.3+)
  id, triggered_by_event_id, severity,
  pattern_matched, llm_narrative, recommendations_json
```

#### 事件与幂等

```
event_inbox
  id, consumer_name, event_id, processed_at
  UNIQUE(consumer_name, event_id)

event_outbox
  id, aggregate_type, aggregate_id, event_type,
  payload_json, published_at
```

### 6.7 索引与分区策略

- `candles / indicator_snapshots / factor_snapshots`：按 `open_time` **月度分区**
- `ai_decisions / orders / trades`：按 `decided_at / submitted_at / closed_at` BTree + `(account_id, trading_mode, symbol)` 复合索引
- `orders.trace_id` UNIQUE
- `agent_invocations`：高频写入，**按月分区**
- `event_outbox`：`published_at IS NULL` 上建部分索引

---

## 7. Control Plane + 前端（Design System 对齐）+ 消息端

### 7.1 Control Plane 服务组成

```
AuthService           JWT + roles
AccountCfgSvc         风控参数 / 币种
SecretVault           Fernet 加密 (API Key / Telegram token)
KillSwitch            一键停机 / 恢复
ManualOpsSvc          手动下单 / 平仓 / 解除熔断
AuditLogger           操作审计
NotifyRouter          多渠道分发（V0.2+）
HealthCheckSvc        /health /readyz
```

**单向依赖**：Control Plane 不直接调 Execution Core；手动操作通过发布 `control.command.*` 事件，Execution Core 订阅执行。

### 7.2 REST API 分组（从 788 行单文件拆分）

```
/api/auth/*          auth_router         (已存在)
/api/admin/*         admin_router        (用户/权限/审计，已存在)
/api/config/*        config_router       (已存在)

/api/account         account_router
/api/positions/*     positions_router    (含手动操作)
/api/orders/*        orders_router
/api/trades/*        trades_router       (含归因过滤)
/api/decisions/*     decisions_router    (含决策回放)
/api/risk/*          risk_router         (事件 + 熔断管理)
/api/reports/*       reports_router

/api/factors/*       factors_router      (V0.2+)
/api/attributions/*  attributions_router (V0.2+)
/api/scores/*        scores_router       (V0.2+)
/api/learning/*      learning_router     (V0.3+)
/api/shadow/*        shadow_router       (V0.3+)
/api/ops/*           ops_router          (V0.3+)

/api/commands/*      commands_router     (手动指令：停机/恢复/平仓)
/api/events/catchup  ws_catchup_router   (WebSocket 断线重放)
```

每 router 独立文件独立测试，`app.py` 只做装配。

### 7.3 前端路由（严格按 AlphaPilot Design System）

Design System 已定义：
- Web Shell：侧栏 240px（品牌+权益+导航+引擎状态）+ 顶栏 60px（标题+风控胶囊+⌘K+铃铛+AUTO）
- 7 个主导航
- 3 种 AI 决策卡 variant（Stepper / Timeline / Graph）
- 禁用 emoji，Lucide 图标
- Mint=盈利/LONG/PASS，Rose=亏损/REJECT，Violet=AI，Amber=DEGRADE/警告

```
(public)
  /login
  /register

(app)  ← 登录后进入 Web Shell
  /                         主控制台（Hero AI 决策卡 + EquitySpark + Positions + EventsFeed）
  /ai                       AI 决策流（按 variant 渲染，Filter 已执行/已拦截/降级/HOLD）
  /positions                持仓与订单（Tabs: 持仓/订单/平仓历史）
  /performance              回测与绩效（权益曲线 vs HODL + 月度 PnL + 策略评分）
  /risk                     策略与风控
    /risk                   硬阈值只读 + 熔断控制
    /risk/strategies        受限策略集（V0.2+）
    /risk/factors           因子库（V0.2+）
    /risk/symbols           交易对管理（迁移自 admin）
    /risk/learning          学习控制器面板（V0.3+）
  /audit                    审计日志 + 日报
  /settings                 个人资料 + 通知订阅 + API Key

(admin)
  /admin/users              现有
  /admin/audit-logs         现有
  /admin/runtime-config     现有
  /admin/prompt-templates   V0.2+

(mobile, V0.2+)
  PWA 只读版（复用 DS Mobile Kit）
```

### 7.4 前端代码结构

```
frontend/src/
├─ styles/
│  └─ design-system.css    ← 复制自 AlphaPilot Design System/colors_and_type.css
├─ components/
│  ├─ ds/                  ← 纯表现层（TypeScript 化 shell.jsx/pages.jsx）
│  │   ├─ shell/AppShell.tsx / Sidebar.tsx / Topbar.tsx
│  │   ├─ atoms/Card.tsx / Stat.tsx / Pill.tsx / Dot.tsx / Spark.tsx / Icon.tsx
│  │   └─ cards/
│  │       ├─ AIDecisionCard.tsx  (variant: stepper/timeline/graph)
│  │       ├─ RiskBannerCard.tsx
│  │       └─ PositionRowCard.tsx
│  └─ domain/              ← 业务组件（组合 ds + hooks）
│      ├─ AccountSummary.tsx
│      ├─ OpenPositionsTable.tsx
│      └─ DecisionFeed.tsx
├─ lib/
│  ├─ api.ts
│  ├─ ws.ts                WebSocket + 重连 + catchup
│  ├─ format.ts            wfmt / wfmtPct / wfmtSigned
│  └─ auth.ts
└─ app/                    Next.js App Router（按 §7.3）
```

**纪律**：
- `ds/` 无业务依赖，可跨项目复用
- 色值一律 `var(--ap-mint)` 等 CSS 变量，不硬编码
- 数字一律 `JetBrains Mono`（DS 规定）
- **禁用 emoji**

### 7.5 UI 交互原则（DS 规定）

- **危险操作二次确认**：
  - 手动平仓：输入币种代号
  - 一键全平：输入 `CLOSE ALL`
  - 解除熔断：输入 `UNLOCK`
- **LLM 延迟占位**：决策区显示"AI 决策生成中..."
- **fallback HOLD**：橘色 Pill 标签
- **高风险环境 Banner**：mainnet 顶栏红色警示
- **语气**：严肃工程化，"已熔断 / 守卫拒绝"，不拟人

### 7.6 消息端协同（V0.2+）

按 PRD 8.1.5：
- **Web 控制台**：承担全部写操作
- **消息端**：只读 + 少量轻指令（Telegram/Slack/Email）
- **安全**：消息端的"写"指令必须经 Web 端二次确认（双通道）

```
NotifyRouter
  订阅 Redis Streams → 按事件+严重度路由到多渠道
  channels: TelegramChannel / SlackChannel / EmailChannel
  订阅策略 per account 可配置
```

默认订阅：

| 严重度 | 事件 | Telegram | Slack | Email |
|-------|------|---------|-------|-------|
| critical | circuit_breaker / api_down | ✅ | ✅ | ✅ |
| warn | stop_loss / decision.rejected | ✅ | ✅ | - |
| info | position.opened/closed | ✅ | - | - |
| debug | decision.proposed (HOLD) | - | - | - |

Telegram Bot 轻指令（V0.3+）：`/status` `/positions` `/pause` `/killall` `/unlock_breaker`——**均需 Web 端确认**。

---

## 8. 交付分期（V0.1 → V1.0）

### 8.1 分期原则

- 每期必须交付**可用的系统**，不是半成品底座
- 每期结束上一期能力**不能退化**（必须有回归测试护栏）
- V0.1 内的"预留"只能是**接口和目录**，不写空实现
- 硬风控边界从第一天就在，不随版本放松
- 所有分期遵循 `CLAUDE.md` 工程工作流（自动 commit+push+deploy-dev）

### 8.2 V0.1 · MVP（跑通自主交易闭环）

**目标**：Binance Testnet 连续运行 7 天不出事，对 BTCUSDT/ETHUSDT 做 AI 自主开多/平多，所有动作可追溯、风控不可绕过、可一键停机。

**包含（P0）**

- 事件与数据底座：Redis Streams + Outbox + `event_outbox / event_inbox`
- 完整数据库 schema（全部表 + `account_id` + `trading_mode` 隔离 + Alembic 迁移）
- 事件契约 dataclass 全集（只发布 ★ 事件）
- 执行核心：ExchangeAdapter + RateLimiter + AccountStateSvc + Guard + OrderExecutor + PositionMonitor
- 策略智能：FactorEngine（6 个预置因子）+ Regime 分类器（基于因子）+ AIT Pipeline 三段式 + Prompt 模板表 + ExperienceRetriever v1（标签检索）+ StrategyRouter（单路由）
- 控制平面：JWT / 角色 / 审计 / SecretVault / 手动操作 / KillSwitch
- 前端：Web Shell + 主控制台 + AI 决策流 + 持仓与订单 + 策略与风控 + 审计日志 + 设置 + WebSocket catchup
- 观察性：/health /readyz + 结构化日志 + 基础 metrics
- 测试：风控规则 100%、LLM 异常 100%、`trace_id` 幂等、Pipeline 集成、PositionMonitor 集成

**不包含**

- Program Trader（仅留接口）
- Shadow Mode
- 参数优化器 / 学习控制器
- Attribution AI（V0.1 只存原始 trade）
- Factor AI / Ops AI（目录不建）
- 消息端
- pgvector
- Review AI LLM 版
- 回测 / HODL 对比
- Mobile PWA

**交付准则**

- 连续 7 天 Testnet 运行不 crash、不穿熔断
- 后端测试全部通过，前端 `npm run build` 零警告
- 所有手动/决策/订单可从 UI 回放到最底层事件
- 一键全平在 2 秒内完成

### 8.3 V0.2 · 归因与消息端

**新增**

- Review AI LLM 版（二次审阅）
- 规则版 Attribution 引擎 → `trade_attributions`
- Strategy Scorer
- Attribution AI 叙事版（日报 LLM 段落）
- Program Trader 三条规则（`trend_following_v1 / breakout_v1 / observation_v1`），StrategyRouter 按 regime 选路
- Prompt 模板 A/B
- NotifyRouter + Telegram + Slack + Email（只读通知）
- AI 决策卡 Timeline / Graph 两种 variant
- 因子启停面板 / 策略评分卡

**不含**：Shadow Mode / 参数自动优化 / 消息端写指令 / pgvector

### 8.4 V0.3 · Shadow Mode + 受控学习

**新增**

- Shadow Runner + Shadow Evaluator
- Historical Validator
- Learning Controller（候选 → 验证 → Shadow → 小流量 → 全量 → 自动回滚）
- `parameter_versions` 版本链
- Ops AI 异常诊断
- Factor AI 占位（`factor_candidates` 开始记录）
- ExperienceRetriever v2（pgvector + Attribution 摘要）
- Telegram Bot 轻指令（双通道确认）
- `/risk/learning` 面板、`/performance` Shadow 对照、Mobile PWA（只读）

### 8.5 V1.0 · 完整受控自进化闭环

**新增**

- Factor AI 自动提案 + 学习控制器激活
- 多智能体完整闭环（Prompt → Decision → Review → Attribution → Ops → Factor 全 LLM 化）
- 合约交易（低杠杆，硬风控约束）
- 学习中心可视化
- 强化经验检索：Prompt 自动注入 top-k 相似经验叙事

**永不包含**：多交易所 / 高频交易 / 链上数据 / 无约束策略自生成 / 强化学习直接实盘

### 8.6 里程碑

- V0.1：Testnet 连续稳定 7 天
- V0.2：归因报告与人工复盘一致率 > 70%
- V0.3：Shadow Mode 累积 100 组对照，学习控制器成功回滚过一次失败变更
- V1.0：Mainnet 小资金连续 30 天无熔断、夏普 > 0.8

---

## 9. 非功能要求

### 9.1 可解释性（PRD 12.1）

每笔交易可从 UI 回放到最底层事件：`trade → position → orders → decision → review → guard → proposal_draft → prompt_template → factors → indicators → candles`。

### 9.2 可审计性（PRD 12.2）

- 所有关键输入 / 输出 / 校验 / 执行 / 学习结果留痕
- `audit_logs` 记录所有手动操作
- `agent_invocations` 记录所有智能体调用
- `parameter_versions` 记录所有学习变更
- 事件 `event_outbox + event_inbox` 保证不丢不重

### 9.3 安全性（PRD 12.3）

- API Key 通过 Fernet 加密存储（`APP_CONFIG_MASTER_KEY`）
- JWT + 角色隔离
- 危险操作二次确认 + 审计
- 消息端写指令双通道确认
- 禁止读取真实 `.env` 文件（CLAUDE.md 规则）
- 风控优先级硬高于模型

### 9.4 稳定性（PRD 12.4）

- Binance API 指数退避重试
- WebSocket 断线重连 + catchup
- LLM 失败 → 兜底 HOLD
- 指标计算失败 → 跳过本轮
- 熔断状态优先级最高
- Outbox 模式保证"业务写成功 ↔ 事件发送"不分裂

### 9.5 幂等性（PRD 12.5）

- 下单 `trace_id = SHA256(decision_id:symbol:action:sequence)`
- 事件消费 `event_inbox(consumer_name, event_id)` UNIQUE
- 订单状态可从 Binance 端恢复
- 止损止盈逻辑可重入

### 9.6 测试策略（PRD 10）

| 层级 | 范围 | 工具 |
|------|------|------|
| 单元 | 指标/风控/Schema/LLM 解析 | pytest |
| 集成 | Pipeline 完整流程 + DB + Redis Streams | pytest + testcontainers |
| API | FastAPI 路由 + WebSocket | pytest + httpx |
| E2E | Binance Testnet 全链路 | 脚本 |

**关键**：风控规则 100% 单元覆盖；LLM 解析异常路径 100% 覆盖；下单幂等专项；Binance Testnet 不 Mock。

### 9.7 部署

- Docker Compose（FastAPI + Postgres + Redis + Next.js）
- 腾讯云日本节点
- `scripts/deploy-dev.sh` 自动部署
- 健康检查 `/health` `/readyz`
- 环境变量模板：`.env.example`

---

## 10. 开放问题

以下问题在实现阶段再决定，不阻塞本设计：

1. **Prompt 模板内容的最终版本**：V0.1 先用现有 `services/decision_engine/prompt.py` 迁入，运行中根据表现迭代
2. **因子权重初始值**：V0.1 等权重，V0.2+ 由 Strategy Scorer 反向修正
3. **pgvector 索引策略**：V0.2+ 引入时根据数据量选 HNSW vs IVFFlat
4. **Shadow Mode 的 KPI 阈值**：V0.3 实装时根据历史 shadow_evaluations 分布决定
5. **合约手数精度 / 杠杆上限**：V1.0 接入合约时与 Binance 规则对齐
6. **消息端选择优先级**：V0.2 起步先做 Telegram（Bot 最简单），Slack/Email 按用户反馈添加

---

## 附录 A：术语表

| 术语 | 含义 |
|------|------|
| **Decision Pipeline** | 15 分钟一次的完整同步执行链 |
| **DecisionProposal** | 策略智能平面的唯一对外产物 dataclass |
| **Factor** | 有语义的结构化信号，归一化到 [-1,1] |
| **Regime** | 市场状态：trending_up / trending_down / ranging / chaotic |
| **Strategy Mode** | 受限策略白名单：ai_trend / ai_breakout / ai_observation / program_* |
| **trace_id** | 同一 Pipeline 所有事件的关联 ID |
| **Outbox 模式** | 业务写 + 事件写同一 DB 事务，后台搬运到 Streams |
| **Learnable** | 参数标签：`false` = 硬风控不可学习，`true` = 学习控制器可修改 |

## 附录 B：关键文件与参考

- PRD：`docs/产品需求文档.md`
- Design System：`AlphaPilot Design System/`
- 旧版设计：`docs/superpowers/specs/2026-03-15-alphapilot-system-design.md`
- 工程工作流：`CLAUDE.md`
- 历史工作日志：`docs/worklog/`
