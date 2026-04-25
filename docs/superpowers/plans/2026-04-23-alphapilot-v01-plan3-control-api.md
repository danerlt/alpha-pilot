# AlphaPilot V0.1 Plan 3 — Control Plane + REST API 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Plan 2 沉淀的业务能力暴露给前端：788 行单文件 `router.py` 拆成 8 个领域 router，新增手动操作（手动平仓/一键全平/解除熔断/手动下单）、KillSwitch、WebSocket 事件回放（catchup）、运行时配置端点。Plan 3 完成后前端 (Plan 4) 可以直接调 REST + WebSocket 而不用碰任何 service 内部。

**Architecture:** 按 spec §7.1-7.2 把控制面拆开。所有写操作走 Plan 2 的事件契约 + OutboxWriter；REST 路由只做参数校验、权限检查、调用 service、返回 response，绝不内含业务逻辑。WebSocket 用 Plan 1 的 RedisStreamsBus 订阅实时事件并广播给前端。

**Tech Stack:** FastAPI、Pydantic v2、SQLAlchemy 2.x、Plan 1 的 RedisStreamsBus / OutboxWriter / InboxGuard、Plan 2 的 OrderExecutor / PositionMonitor。

**Spec 参考:** `docs/superpowers/specs/2026-04-21-alphapilot-v1-system-design.md` §7。

---

## File Structure

### 创建

```
backend/src/
├── control/                          ← Control Plane
│   ├── __init__.py
│   ├── kill_switch/
│   │   ├── __init__.py
│   │   └── service.py                KillSwitchService (停机/恢复)
│   ├── manual_ops/
│   │   ├── __init__.py
│   │   └── service.py                ManualOpsService (手动平仓/一键全平/解熔断)
│   └── notifier/
│       ├── __init__.py
│       └── router.py                 NotifyRouter (V0.2+ 占位，Plan 3 只建结构)
│
└── app/
    └── routers/                      ← 拆分自旧 app/router.py
        ├── __init__.py
        ├── auth.py                   /api/auth/*    (从 router.py 抽出)
        ├── account.py                /api/account
        ├── positions.py              /api/positions/*
        ├── trades.py                 /api/trades
        ├── decisions.py              /api/decisions
        ├── risk.py                   /api/risk-events/*
        ├── reports.py                /api/reports/*
        ├── orders.py                 /api/orders   (新)
        ├── factors.py                /api/factors  (新, 读因子快照)
        ├── commands.py               /api/commands/* (新, 手动操作)
        ├── runtime_config.py         /api/config/runtime (从 router.py 抽出)
        ├── admin.py                  /api/admin/*   (从 router.py 抽出)
        ├── ws_catchup.py             /api/events/catchup (新, WebSocket 断线重放)
        └── health.py                 /health, /api/health
```

### 修改

```
backend/src/app/app.py                导入新 routers, 替换旧 from app.router
backend/src/app/router.py             保留作为 facade, 重新 export 所有子 router
backend/src/app/websocket.py          消费新事件流 + catchup 接口
```

---

## Conventions

1. **每个 router 文件 < 200 行**；超过就拆。
2. **router 函数体只做：** 参数校验 → 调 service → 转 schema → 返回；不包含业务逻辑。
3. **手动操作必写 `audit_logs`** + `manual.override` outbox 事件。
4. **路由权限**：`/api/admin/*` 要 admin role；`/api/commands/*` 至少 user 已登录；`/api/auth/*` 公开。
5. **测试**：每个 router 至少 1 个 happy path + 1 个权限路径 + 1 个错误路径。

---

## Part A · Router 拆分

### Task A1: 健康检查 + auth router 抽出
- 把 `/health`, `/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/auth/me` 从 `app/router.py` 移到 `app/routers/health.py` + `app/routers/auth.py`
- 新建 `app/routers/__init__.py`，逐步在 `app.py` 里 `include_router` 替换
- 测试：保留 `tests/api/test_auth.py`、`test_health.py` 不动，确认通过。

### Task A2: account / positions / orders / trades / decisions / risk / reports
- 按 router.py 现有路由前缀拆 7 个文件
- 每个文件包含原有路由 + 对应 Pydantic response schema（在文件顶部）
- 测试：复用既有 tests/api/* 测试不动

### Task A3: admin + runtime_config
- 把 `/api/admin/*` 4 个端点 + `/api/config/runtime` 2 个端点抽出
- 测试：tests/api/test_admin_*, test_runtime_config.py 不变

### Task A4: 旧 app/router.py 减为 facade
- 内容只剩 `from .routers import *` + 注释说明本文件已废弃, 留作 BC

## Part B · 新增手动操作端点

### Task B1: ManualOpsService
- `manual_close_position(position_id, reason, operator_user_id)` — 不走 Guard, 直接 OrderExecutor.close_long
- `manual_close_all(operator_user_id)` — 紧急通道, 平掉账户所有 open positions
- `manual_open_long(symbol, qty, sl, tp, reason, operator_user_id)` — 走 Guard 但跳过 Review (V0.1 必填风控参数)
- `manual_resolve_circuit_breaker(event_id, reason, operator_user_id)` — 写 risk_events.resolved=true

每个动作都写 `audit_logs` + 发 `manual.override` outbox 事件。

### Task B2: KillSwitchService
- 全局 `paused/active` 状态存 `system_settings` (key=`kill_switch_state`)
- `pause(operator_user_id, reason)` / `resume(operator_user_id, reason)`
- 暂停时 strategy_pipeline / position_monitor 都跳过 (workers 启动时检查)
- 状态查询 + `audit_logs`

### Task B3: commands router
- `POST /api/commands/close-position/{id}` → ManualOpsService.manual_close_position
- `POST /api/commands/close-all` → manual_close_all (要求 body 有 `confirmation: "CLOSE ALL"`)
- `POST /api/commands/open-long` → manual_open_long
- `POST /api/commands/resolve-breaker/{id}` → resolve
- `POST /api/commands/pause` / `POST /api/commands/resume` → KillSwitch
- `GET /api/commands/kill-switch` → 当前状态

### Task B4: factors / orders / catchup 新端点
- `GET /api/factors?symbol=BTCUSDT&limit=10` → 最新因子快照
- `GET /api/orders?status=filled&limit=50` → 订单列表
- `GET /api/events/catchup?since=<event_id>` → 从 Redis Streams 重放断线期间事件

## Part C · WebSocket 升级

### Task C1: 多事件通道订阅
- 重写 `app/websocket.py`: 订阅 Redis Streams 的多个流 (`decision.proposed`, `position.opened`, `position.closed`, `trade.closed`, `risk.event.triggered`, `circuit_breaker.triggered`)
- 客户端连接时按账户订阅对应消息

### Task C2: 断线 catchup
- 客户端断线重连时带 `?since=<last_event_id>`
- 服务器从 Redis Streams XRANGE 重放 since 后的事件
- 5 分钟 / 500 条限制 (Plan 1 spec §3.5)

## Part D · 部署脚本调整

### Task D1: 在 app.py lifespan 里启动 strategy_pipeline + position_monitor APScheduler
- 用 Plan 2 的 `run_strategy_pipeline_once` / `run_position_monitor_once`
- 间隔: `STRATEGY_LOOP_INTERVAL_MINUTES` / `POSITION_MONITOR_INTERVAL_SECONDS`
- 启动前先检查 KillSwitch 状态

---

## 自检清单

- [ ] router.py 主文件 < 100 行 (剩 facade 注释)
- [ ] 8 个新 router 文件每个 < 200 行
- [ ] 所有手动操作有 audit_logs + manual.override 事件
- [ ] commands router 测试覆盖每条命令
- [ ] WebSocket catchup 集成测试通过 (testcontainers Redis)
- [ ] APScheduler 启动后能调用 Plan 2 worker
