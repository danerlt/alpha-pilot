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

## Phase 3: PENDING — Frontend + WebSocket + Migration

### Remaining Work for V0.1 MVP

1. **Database migration** — Run `make init-db && make upgrade-db` to create all 11 tables
2. **WebSocket handler** in FastAPI (Redis Pub/Sub → WebSocket push to frontend)
3. **Next.js Frontend** — Real-time Dashboard:
   - Dashboard: positions panel, PnL chart, decision log, regime display
   - Manual ops: close-all button, manual close, circuit breaker toggle
   - WebSocket client for real-time updates
4. **Unit tests** — parser (fallback cases), guard (circuit breaker rules), indicators

## Auto-commit Policy

After each chunk is complete, commit with message: `feat: implement <chunk name>`

## To Resume on New Machine

See `CLAUDE.md` in project root for full restore instructions.
