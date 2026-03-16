---
name: AlphaPilot project overview
description: AlphaPilot AI autonomous crypto trading system — architecture, stack, and restore instructions
type: project
---

# AlphaPilot 项目概览

AlphaPilot 是一个 AI 自主数字货币交易系统，面向 Binance 现货市场，V0.1 仅支持做多。

**Why:** 用户希望构建一个受控风险框架下的 AI 自主交易系统，支持跨机器通过 Claude 恢复上下文。

**How to apply:** 每次对话开始时读取本记忆，了解项目全局状态，继续未完成的实现。

---

## 仓库路径

`/workspace/alpha-pilot`

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic |
| 调度 | APScheduler（内嵌 FastAPI） |
| LLM | Claude (claude-opus-4-6) / OpenAI，可配置 |
| 交易所 | Binance Testnet + Mainnet（python-binance） |
| 数据库 | PostgreSQL 16 |
| 缓存/事件总线 | Redis 7（含 Pub/Sub） |
| 部署 | Docker Compose |
| 包管理 | uv |

## 核心架构：双循环

1. **策略循环（15min）**: market_data → account_state → indicators → regime → experience_store → decision_engine → execution_guard → order_execution → monitoring → reporting → Redis Pub/Sub
2. **持仓监控循环（10s）**: 检查止损穿透 → 检查止盈成交 → 检查日内亏损 → 检查ATR/波动率 → Redis推送告警

## 目录结构

```
backend/src/
├── app/          # FastAPI 入口 + 路由
├── services/     # 核心业务服务（待实现）
│   ├── market_data/
│   ├── account_state/
│   ├── indicators/
│   ├── regime/
│   ├── decision_engine/
│   ├── execution_guard/
│   ├── order_execution/
│   ├── monitoring/
│   ├── experience_store/
│   └── reporting/
├── workers/      # APScheduler 工作循环（待实现）
└── shared/       # 配置、DB、枚举、ORM模型（已完成）
    ├── config.py
    ├── db.py
    ├── enums.py
    └── models/   # 11个表（candles, positions, ai_decisions, orders, trades, etc.）
```

## 数据库表（已建模，待迁移）

- candles, indicator_snapshots, regime_snapshots, account_snapshots
- positions, ai_decisions, orders, trades
- risk_events, experience_store, daily_reports

## 关键设计原则

- 所有表有 `trading_mode` 字段（testnet/mainnet 数据隔离）
- 下单使用 `trace_id` 幂等（decision_id + symbol + action 哈希）
- LLM 输出保存完整 prompt 和 raw_output 用于审计
- JSON 解析失败/字段缺失/动作非法 → 统一回退 HOLD
- 熔断规则不可被 LLM 覆盖（日亏损超限、连续亏损3笔、API异常）

## 环境变量（.env.example 已在根目录）

TRADING_MODE, BINANCE_API_KEY, BINANCE_API_SECRET, LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, DATABASE_URL, REDIS_URL, MAX_POSITION_SIZE_PCT, MAX_DAILY_LOSS_PCT, MAX_CONSECUTIVE_LOSSES, MAX_SINGLE_RISK_PCT

## 工程过程记录

除了 git 历史外，自动推进的工程性工作需要同步记录到 `docs/worklog/` 目录，尤其是：
- 测试/迁移/部署收口
- 文档状态校正
- 低风险控制台保护增强
- 其他不直接体现在 PRD 但会影响后续接手效率的工作

建议按日期/主题拆分文件，例如：`docs/worklog/2026-03-17-phase3-closeout.md`

## 开发命令

```bash
make dev-up         # 启动 Docker（DB + Redis）
make dev-backend    # 启动 FastAPI（热重载）
make init-db        # 初始化数据库迁移
make upgrade-db     # 运行迁移
make test           # 运行所有测试
```

## 版本路线图

- V0.1: 自动交易闭环 + 全栈 Dashboard（现货做多）← 当前目标
- V0.2: 监控面板增强、风控中心、告警通知
- V0.3: 参数优化器、Shadow Mode、合约支持
