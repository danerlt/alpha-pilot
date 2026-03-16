---
name: AlphaPilot Phase 2 implementation status
description: Phase 2 core services implementation — what's done, what's pending, and approach
type: project
---

# AlphaPilot Phase 2: Core Services Implementation

**Why:** Phase 1 (foundation) is complete. Phase 2 implements all core trading services.

**How to apply:** When resuming work, check this file to see what's been implemented and what's pending. Always continue from the last completed chunk.

---

## Phase 1 Status: COMPLETE ✅

Foundation: DB models (11 tables), FastAPI skeleton, health endpoint, Alembic setup, Docker Compose, Makefile, pytest structure.

## Phase 2 Status: COMPLETE ✅

All core services committed to git (commits 1ad3acd and 6c6a8ec on `main`).

### Completed Services

| Service | Files | Status |
|---------|-------|--------|
| market_data | binance_client.py, candle_service.py | ✅ |
| account_state | service.py | ✅ |
| indicators | calculator.py (EMA20/50/200, RSI, MACD, ATR, BB, volatility) | ✅ |
| regime | classifier.py (trending_up/down, ranging, chaotic) | ✅ |
| decision_engine | prompt.py, parser.py, engine.py | ✅ |
| execution_guard | guard.py (PASS/REJECT/DEGRADE, circuit breaker) | ✅ |
| order_execution | executor.py (open_long, close_long, trace_id idempotent) | ✅ |
| monitoring | monitor.py (SL check, TP poll, daily loss circuit breaker) | ✅ |
| experience_store | store.py (record + retrieve) | ✅ |
| reporting | reporter.py (daily report generation) | ✅ |
| workers | strategy_loop.py (15m), position_monitor.py (10s) | ✅ |
| app/main.py | APScheduler lifespan wired in | ✅ |
| app/router.py | REST endpoints (positions, trades, decisions, risk events, reports, account) | ✅ |

## Phase 3: IN PROGRESS — 已进入收口/稳态化阶段

### Current Reality for V0.1 MVP

1. **Database migration** — 已补首个 Alembic 初始迁移；后续重点是持续维护迁移链而不是继续用“待实现”描述
2. **WebSocket handler** — 已在 FastAPI 中实现（Redis Pub/Sub → WebSocket push）
3. **Next.js Frontend** — 已有可用实时 Dashboard：持仓、风险事件、决策日志、实时事件流、手动平仓操作
4. **Tests** — backend 测试已跑通（53 passed）；后续优先补前后端联调、执行链路和部署路径相关验证

### Remaining Work

- 收口部署路径与 WebSocket 稳定性
- 加强危险操作保护与审计
- 继续补前端/集成级回归测试
- 对齐 README / CLAUDE / 记忆文件与真实代码状态

## Auto-commit Policy

After each chunk is complete, commit with message: `feat: implement <chunk name>`

## To Resume on New Machine

See `CLAUDE.md` in project root for full restore instructions.
