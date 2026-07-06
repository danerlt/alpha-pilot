# webapp ⇄ 后端真联调 · 后端待办清单

> **2026-07-06 前端契约刷新完成**（4 个 commit：核心域/绩效/行情流+实验室/设置+2FA），
> 66 paths 已全量吃上，全部兼容代码已删。**新增缺口 #8**：
>
> | # | 缺口 | 前端现状 | 建议 |
> |---|------|----------|------|
> | 8 | **WS 握手只认 `?token=` 不读 cookie**（`/ws` 与 `/ws/market` 的 `_verify_token`） | 登录响应的 access_token 仅内存持有（`webapp/src/api/tokenStore.ts`），页面刷新后 WS 实时降级直到重新登录（REST 不受影响） | WS 握手增加 cookie（`ap_token`）回退：浏览器同源 WS upgrade 自动带 cookie，改一处 `_verify_token` 入参来源即可；落地后前端删 tokenStore |
> | 9 | **策略受限集启停端点缺失**（`GET/PATCH /api/strategies`） | 策略与风控页「受限策略集」启停仍 mock-only（`strategyApi.list/toggle`） | 新增策略列表+启停端点（或用 symbol_config/runtime config 表达策略开关）；落地后前端接真 |
> | 10 | **日报无 LLM 叙述字段** | 审计页 AI 日报卡由统计合成叙述（`fromWireReport`） | DailyReport 增 `narrative` 字段（attribution.narrative 过渡→LLM）；落地后前端直用 |
>
> **前端 66 paths 已全量接真；上述 #8/#9/#10 落地后 webapp 无 mock 兜底残留。**

> **状态更新（2026-07-06 后端会话）**：**清单 #1-7 全部收口** ✅，openapi.json 已重导（66 paths），
> 前端 `npm run gen:api` 后可删全部兼容代码。
> - #1-4/6/7 见 2026-07-05 批次（`GET /api/account/history` / `GET /api/orders` /
>   `GET /api/risk/limits`；DecisionRead.guard_verdict、PositionRead.strategy_mode/position_pct、
>   CatchupOut）
> - **#1 顺带**：决策列表读已直出 `entry_price/stop_loss/take_profit/position_size_pct`（决策卡五格）
> - **#5**：`GET /api/performance/summary` 已含 sharpe/sortino/win_rate/today_trades/
>   avg_holding_seconds/week_pnl/month_pnl + vs HODL 曲线（P6 落地）
> - 「已在后端计划内」三项也已全部落地：P2b `/ws/market` 代理、P4 RBAC+2FA、
>   P6 performance 三接口（`/api/performance/{summary,monthly,attribution}`）。绩效页可全量接真。

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


## 浏览器级验收发现（2026-07-06 后端会话，转前端处理）

> **已全部修复并复验（2026-07-06 后端会话代修）**：① 后端 WS 支持 ap_token cookie 回退（前端
> 内存 token 可整体移除，见 marketStream/stream 的 token 注释）；② 权限键统一 `trade.manual_order`；
> ③ favicon.svg + `GET/PATCH /api/strategies` 真端点（守卫 strategy_enabled 真实生效）。
> openapi 已重导（68 paths），`npm run gen:api` 可更新类型。原始记录：

1. **行情 WS 未带 token**：`/ws/market` 连接需追加 `?token=<jwt>`（与 `/ws` 一致），当前 403 → 盘口/逐笔不渲染
2. 行情页下单按钮文案「无手动下单权限」：admin 登录态下出现，疑似 usePermission 判断或与预检 REJECT 状态的文案混用
3. 登录页 ×1 / 风控页 ×2 的 404 资源（favicon 类 + mock-only 旧路径）清理
