# webapp 前端架构定稿 · 后端配合 B1-B3 适配计划

> 依据：`docs/webapp前端架构.md` §3 后端配合清单（2026-07-05 老板批准定稿）。
> B1 的导出脚本 `backend/scripts/export_openapi.py` 前端会话已建好，本计划做其余增量。
> 执行方式：本会话内联 TDD，每 task 提交+推送。

## Task 1 · B1a：operation_id 稳定化

- `src/app.py`：include_router 后调用 `_use_route_names_as_operation_ids(app)`，
  将每个 APIRoute 的 operation_id 设为函数名；重名函数先改名保证全局唯一。
- 测试 `tests/api/test_openapi_contract.py`：全部 APIRoute 的 operation_id 唯一且等于 endpoint 函数名。
- 重导 `docs/api/openapi.json`。

## Task 2 · B2：risk.state / account.snapshot 事件 + GET /api/risk/state

- contracts：`RiskState`（state: OK|WARN|HALTED, day_loss_pct, positions_pct, regime）、
  `AccountSnapshotTaken`（total/available/unrealized/daily_pnl/daily_pnl_pct, snapshot_at）入注册表。
- `RiskStateService`（`src/services/risk/risk_state.py`）：compute() 聚合
  kill_switch/未解决熔断 → HALTED；day_loss ≤ -50%×上限 → WARN；否则 OK；
  day_loss_pct 取最新账户快照；positions_pct = Σ开仓市值/总权益；regime 取最新快照。
  publish() 写 outbox `risk.state`。
- 发布点：`ManualOpsService` pause/resume/resolve_breaker 之后；`PositionMonitor` 熔断触发后。
- `AccountStateService.sync_snapshot` 增加可选 outbox，快照落库后发 `account.snapshot`。
- 端点 `GET /api/risk/state`（risk 域，登录可见）返回 compute() 结果。

## Task 3 · B3：cookie 认证 + logout + 权限矩阵

- login：注入 fastapi Response，`set_cookie("ap_token", jwt, httponly=True, samesite="lax",
  secure=<ENVIRONMENT in uat/prod>, max_age=令牌有效期)`；返回体不变（Bearer 并存）。
- `get_current_user`：Authorization 头缺失时回退读 `ap_token` cookie。
- `POST /api/auth/logout`：delete_cookie + 返回 {ok: true}。
- 权限矩阵常量 `src/services/system/permissions.py`：按设计稿 admin.jsx PERMS
  （交易/策略/系统三组 × owner/admin/trader/viewer），另附 `role_aliases: {"user": "trader"}`
  （P4 RBAC 前的过渡映射；端点强制仍走 require_admin，本矩阵仅 UI 展示与前端 usePermission）。
- `GET /api/admin/roles`（登录可见，非仅 admin——viewer 也要知道自己不能做什么）。

## Task 4 · B1b：核心端点显式响应模型（逐步收敛的第一批）

- 新增 read 模型并在路由挂 `response_model=Response[...]`：
  positions / trades / account / decisions 列表 / risk-events / market klines·ticker·symbols /
  orders precheck·place / risk/state / auth login·me / admin roles。
- 字段与现返回 dict 逐 key 一致（既有 API 测试兜底防字段丢失）。
- 完成后重导 openapi.json。

## Task 5 · 收口

全量回归 + ruff + 重导 openapi.json + worklog + 更新记忆。
