# webapp ⇄ 后端真联调 · 后端待办清单

> **状态更新（2026-07-05 后端会话）**：#1-4、#6、#7 已全部收口（commit 见 git log
> `feat(api): webapp 联调缺口收口`），openapi.json 已重导（48 paths），前端可
> `npm run gen:api` 后删对应兼容代码。#5（周/月 PnL/Sharpe 等聚合指标）按清单建议留 P6 绩效期。
> 新增端点：`GET /api/account/history`、`GET /api/orders`、`GET /api/risk/limits`；
> 补字段：DecisionRead.guard_verdict、PositionRead.strategy_mode/position_pct；
> catchup 已挂 CatchupOut response_model（可删形状嗅探）。

> 2026-07-05 前端会话完成 wire 适配层后，对**真实后端**（隔离库 `alphapilot_webapp_it`）
> 跑通浏览器级联调：登录（ap_token cookie）→ 2FA → 主控台/行情/决策流/持仓 全部正常、
> 零控制台错误。以下是联调发现的**后端缺口**，按前端影响排序，供后端会话逐项收口。
> 每项完成后：重导 OpenAPI（`uv run python scripts/export_openapi.py`）→ 通知前端
> `npm run gen:api` + 删对应兼容代码（位置都标在下面）。

## 高优先（影响页面正确性）

| # | 缺口 | 前端现状（临时兼容） | 建议 |
|---|------|---------------------|------|
| 1 | **DecisionRead 缺守卫裁决字段**（PASS/REJECT/DEGRADE） | `wire.ts fromWireDecision` 以 `is_fallback` 近似（fallback→DEGRADE 否则 PASS），决策流"已拦截"过滤语义不准 | DecisionRead 增加 `guard_verdict` 字段（detail 已可由 guard_events 推导，列表读需要直出）；顺带建议列表读补 `entry_price/stop_loss/take_profit/position_size_pct`，决策卡头部五格才有数据 |
| 2 | **GET /api/account/history 缺失**（权益曲线序列） | 真实模式 404 容错为空，曲线仅靠 `account.snapshot` 事件增量生长（刷新即清空） | 新增端点：按 account_snapshots 表返回近 N 点 `[{ts, equity}]` |
| 3 | **GET /api/orders 订单列表缺失**（持仓页订单簿表） | 前端走 mock-only 占位路径 `/api/orders/list`，真实模式 404 容错为空 | 新增 `GET /api/orders?limit=`（近 N 条 Order，含 status） |

## 中优先（字段补齐）

| # | 缺口 | 前端现状 | 建议 |
|---|------|----------|------|
| 4 | PositionRead 缺 `strategy_mode`、仓位占比 | 持仓表"策略"列显示 —，marginPct=0 | 补两字段（decision 反查可得 strategy_mode） |
| 5 | AccountSnapshotRead 缺周/月 PnL、Sharpe、胜率、今日交易数、平均持仓 | 主控台四磁贴+权益卡周/月归零展示 | P6 绩效期覆盖；或先在 account 端点补 trades 聚合的轻量版 |
| 6 | `/api/events/catchup` 无 response_model | `services.ts toEventItem` 做形状嗅探（EventItem 直出 vs EventEnvelope 两态兼容） | 补 `list[EventEnvelopeRead]` response_model，前端即可删嗅探 |
| 7 | `GET /api/config/runtime` 出参与前端硬风控表（HardLimit[]）不同构 | 风控页硬风控表仍 mock-only | 提供只读风控阈值视图端点或确认复用 runtime config 的字段映射 |

## 已在后端计划内（不重复排期，仅备注前端依赖）

- **P2b** `market.{symbol}` WS 代理 → 行情页盘口/逐笔（现 mock-only：`/api/market/depth|trades` 占位路径）
- **P4** RBAC 落表 + 2FA → `fromWireUser` 的 `twoFa=false/lastActive="—"` 占位即可换真值；手动下单权限从 require_admin 放宽 trader+
- **P6** performance 三接口 → 绩效页整页仍 mock

## 联调环境复现（后端会话验证用）

```powershell
# 隔离库（不污染 dev 数据）
docker exec alpha-pilot-postgres-1 createdb -U alphapilot alphapilot_webapp_it
cd backend
$env:DATABASE_URL='postgresql://alphapilot:alphapilot@localhost:5442/alphapilot_webapp_it'
$env:REDIS_URL='redis://localhost:6389/5'
$env:ALPHAPILOT_SKIP_SECRET_VALIDATION='1'
$env:DEFAULT_ADMIN_EMAIL='admin@example.com'; $env:DEFAULT_ADMIN_PASSWORD='<自定>'
.\.venv\Scripts\python.exe -m alembic -c src/db/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m uvicorn src.app:app --port 8000
# 前端（同源代理，cookie 直通）：cd webapp && npm run dev:real  → http://localhost:5174
```

## 前端侧对应实现（后端改完后要动的位置）

- 适配层：`webapp/src/api/wire.ts`（fromWire*）/ `webapp/src/api/mocks/wireMocks.ts`（mock 同构）
- 占位路径与嗅探：`webapp/src/api/services.ts`（`/api/orders/list`、`toEventItem`、history 注释）
- 契约再生成：`cd webapp && npm run gen:api`
