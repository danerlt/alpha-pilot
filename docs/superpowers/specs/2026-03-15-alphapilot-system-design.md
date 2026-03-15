# AlphaPilot 系统设计文档

> 日期：2026-03-15
> 项目：AlphaPilot — 面向 Binance 的 AI 自主数字货币交易系统
> 范围：V0.1 MVP 全栈设计

---

## 1. 项目定位

AlphaPilot 是一个在严格风控和受限策略框架下，实现 AI 自主决策、自动执行、交易复盘与受控进化的数字货币交易系统。

核心价值：**自主决策 · 风控约束 · 执行闭环 · 受控进化**

---

## 2. 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python + FastAPI |
| 前端 | TypeScript + Next.js |
| 数据库 | PostgreSQL |
| 缓存 / 事件总线 | Redis（含 Pub/Sub） |
| 调度 | APScheduler（内嵌 FastAPI） |
| LLM | 可配置（Claude / GPT / 本地模型） |
| 交易所 | Binance Testnet + Mainnet |
| 部署 | Docker Compose → 腾讯云日本节点 |

---

## 3. 仓库结构

```
alpha-pilot/
├── backend/
│   ├── src/
│   │   ├── app/                # FastAPI 应用入口、路由、WebSocket Handler
│   │   ├── services/
│   │   │   ├── market_data/    # Binance 行情接入
│   │   │   ├── account_state/ # 账户状态
│   │   │   ├── indicators/    # 技术指标计算
│   │   │   ├── regime/        # 市场状态识别
│   │   │   ├── decision_engine/  # AI 决策引擎
│   │   │   ├── execution_guard/  # 风控与执行守卫
│   │   │   ├── order_execution/  # 下单执行
│   │   │   ├── monitoring/    # 持仓与收益监控
│   │   │   ├── experience_store/ # 经验库
│   │   │   └── reporting/     # 日志与复盘
│   │   ├── workers/           # APScheduler 主交易循环
│   │   └── shared/            # schemas、prompts、configs、enums
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── api/
│   ├── migrations/            # Alembic migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── scripts/               # init_db.py, upgrade_db.py 等
│   └── alembic.ini
├── frontend/                  # Next.js（按前端规范）
├── docker/                    # Docker Compose、部署配置
├── Makefile                   # 统一命令入口
└── docs/
```

---

## 4. 整体架构

### 运行时组件

```
┌─────────────────────────────────────────────┐
│               Docker Compose                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ FastAPI  │  │ Next.js  │  │ Postgres │  │
│  │  :8000   │  │  :3000   │  │  :5432   │  │
│  └────┬─────┘  └────┬─────┘  └──────────┘  │
│       │WebSocket     │REST                  │
│       └──────┬───────┘        ┌──────────┐  │
│              │                │  Redis   │  │
│  ┌───────────▼──────────┐     │  :6379   │  │
│  │  Trading Loop Worker │◄────┤Pub/Sub   │  │
│  │   (APScheduler)      │────►│          │  │
│  └──────────────────────┘     └──────────┘  │
└─────────────────────────────────────────────┘
```

### 前后端交互

- **REST API**：历史数据查询、配置管理、手动操作指令
- **WebSocket**：实时推送持仓、盈亏、AI 决策、风控事件
- **Redis Pub/Sub**：内部事件总线，交易循环 → FastAPI WebSocket → 前端

---

## 5. 核心数据流

### 双循环架构

#### 策略循环（15m / 1h 触发）

```
1. market_data      → 拉取 K线、价格、成交量
2. account_state    → 拉取账户余额、持仓、订单
3. indicators       → 计算 EMA/RSI/MACD/ATR/布林带
4. regime           → 识别市场状态（趋势/震荡/混乱）
5. experience_store → 检索相似历史经验摘要
6. decision_engine  → LLM 生成结构化交易决策 JSON
7. execution_guard  → 风控校验（PASS / REJECT / DEGRADE）
8. order_execution  → 自动下单 / 止损 / 止盈 / 平仓
9. monitoring       → 更新持仓、收益状态
10. reporting       → 写入日志、经验库
11. Redis Pub/Sub   → 推送事件给前端
```

#### 持仓监控循环（每 5~10 秒触发）

```
检查止损价是否被穿透   → 立即平仓
检查日内亏损是否超限   → 触发熔断
检查 ATR/波动率异常   → 降级或暂停
检查 API 连接状态     → 异常停机
→ Redis Pub/Sub       → 推送告警给前端
```

### Testnet / Mainnet 切换

```
TRADING_MODE=testnet  → Binance Testnet（testnet.binance.vision）+ 测试 Key
TRADING_MODE=mainnet  → Binance Mainnet（api.binance.com）+ 真实 Key
```

两套环境 API 接口完全一致，所有业务逻辑代码不做任何分支处理。

---

## 6. 手动操作能力

前端提供人工兜底操作面板，跳过 AI 决策直接执行，经过执行守卫：

| 类别 | 操作 |
|------|------|
| 紧急操作 | 一键全部平仓、一键停机、一键恢复 |
| 仓位管理 | 手动平仓指定持仓、调整止损止盈、部分平仓 |
| 手动下单 | 手动开仓（市价/限价） |
| 风控干预 | 手动触发熔断、手动解除熔断 |

**原则**：一键停机和一键全平优先级最高，立即中断所有自动循环。所有手动操作写入审计日志。

---

## 7. AI 决策 Schema

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "action": "OPEN_LONG | CLOSE_LONG | HOLD",
  "confidence": 0.78,
  "entry_type": "MARKET | LIMIT",
  "entry_price": 68250,
  "stop_loss": 67380,
  "take_profit": 69800,
  "position_size_pct": 0.12,
  "strategy_mode": "trend_following | breakout | observation",
  "reasoning": ["1h趋势向上", "MACD金叉"],
  "risk_note": "波动率上升，仓位控制在12%"
}
```

**兜底机制**：JSON 解析失败、字段缺失、止损缺失、动作非法 → 统一回退 `HOLD`。

---

## 8. 核心数据库表

| 表名 | 职责 |
|------|------|
| `candles` | K线历史数据 |
| `indicator_snapshots` | 每次循环的指标快照 |
| `regime_snapshots` | 市场状态识别结果 |
| `account_snapshots` | 账户余额与权益快照 |
| `positions` | 当前持仓 |
| `ai_decisions` | 每次 AI 决策完整记录（含完整 prompt 输入） |
| `orders` | 下单记录与执行结果 |
| `trades` | 完整交易记录（开仓到平仓） |
| `risk_events` | 风控事件与熔断记录 |
| `experience_store` | 交易经验库 |
| `daily_reports` | 每日复盘报告 |

**关键设计原则**：
- 所有表含 `trading_mode`（testnet/mainnet），数据完全隔离
- 所有下单使用 `trace_id` 保证幂等，防止重复下单
- `ai_decisions` 保存完整 prompt 输入和 JSON 输出，便于审计

---

## 9. 错误处理与稳定性

| 层级 | 故障场景 | 处理方式 |
|------|---------|---------|
| Binance API | 超时/限频/断线 | 指数退避重试，失败暂停循环 |
| LLM 调用 | 超时/解析失败/字段缺失 | 统一回退 HOLD，记录异常 |
| 指标计算 | 数据不足/计算异常 | 跳过本轮，等待下一周期 |
| 执行守卫 | 风控拦截 | 返回 REJECT/DEGRADE，记录原因 |
| 下单执行 | 下单失败/部分成交 | 幂等重试（trace_id 防重），失败告警 |
| 持仓监控 | 止损穿透/波动异常 | 秒级触发紧急平仓，熔断保护 |
| WebSocket | 前端断线 | 自动重连，断线期间事件缓冲到 Redis |

### 熔断规则（最高优先级，不可被覆盖）

- 日亏损超限 → 自动熔断，停止策略循环，保留持仓监控
- 连续亏损 3 笔 → 自动熔断
- API 异常持续 → 自动停机
- 人工一键停机 → 立即中断所有循环

---

## 10. 测试策略

| 层级 | 范围 | 工具 |
|------|------|------|
| 单元测试 | 指标计算、风控规则、Schema 校验、LLM 输出解析 | pytest |
| 集成测试 | 交易循环完整流程、DB 读写、Redis Pub/Sub | pytest + testcontainers |
| API 测试 | FastAPI 路由、WebSocket 推送 | pytest + httpx |
| E2E 测试 | Binance Testnet 全链路 | 手动 + 脚本 |

**关键原则**：
- 风控规则必须 100% 单元测试覆盖
- LLM 输出解析必须覆盖所有异常路径
- 下单幂等性必须有专项测试
- Binance Testnet 作为集成环境，不用 Mock

---

## 11. V0.1 MVP 范围（P0 功能）

1. Binance Testnet + Mainnet 接入（BTCUSDT、ETHUSDT，15m/1h）
2. 技术指标计算（EMA/RSI/MACD/ATR/布林带/波动率）
3. 市场状态识别（trending_up / trending_down / ranging / chaotic）
4. AI 结构化交易决策（可配置 LLM，固定 schema 输出）
5. 受限策略框架（趋势跟随 / 突破确认 / 观望）
6. 执行守卫（风控校验，PASS / REJECT / DEGRADE）
7. 自动下单与平仓（含止损止盈，幂等保护）
8. 基础风控熔断（日亏损 / 连续亏损 / API 异常）
9. 双循环架构（策略循环 + 秒级持仓监控）
10. 持仓与收益监控（实时推送）
11. 交易日志与复盘记录
12. 经验库（基础版）
13. 前端 Dashboard（实时监控 + 手动操作面板）

---

## 12. 版本路线图

| 版本 | 目标 |
|------|------|
| V0.1 | 跑通自动交易闭环 + 全栈 Dashboard |
| V0.2 | 监控面板增强、风控中心、告警通知、策略评分器 |
| V0.3 | 参数优化器、Shadow Mode、自动回滚、更多币种 |
| V1.0 | 完整受控自进化闭环 |
