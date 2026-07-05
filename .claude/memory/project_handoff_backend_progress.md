# handoff 后端实现进度（跨会话续接锚点）

> 最后更新：2026-07-05。后端会话按 `AlphaPilot Design System/handoff/` 交付包实现服务端，
> 前端由并行会话做 webapp/。测试基线 **615 passed + 2 skipped**。

## 已完成

| 期 | 内容 | worklog / 计划 |
|----|------|----------------|
| P1 | `decision.progress`（5阶段流式）/`decision.complete` 事件 + `DecisionProgressEmitter`（独立会话即时 commit）+ `GET /api/decisions/{id}` 详情 + `risk_events.decision_id` 列 | `docs/worklog/20260705_1540_*.md` |
| P2 (REST) | market 域三接口（klines/ticker/symbols）+ 守卫 `evaluate()` 逐项重构（check 行为逐字不变，预检/实盘同源）+ 手动下单三接口（precheck / POST /api/orders 幂等 manual trace / PATCH sltp） | `docs/worklog/20260705_1720_*.md` |
| webapp B1-B3 | operation_id=函数名 + 核心 15 端点显式 response_model + risk.state/account.snapshot 事件 + `GET /api/risk/state` + httpOnly cookie（ap_token）并存 Bearer + logout + `GET /api/admin/roles` 权限矩阵 | `docs/worklog/20260705_1830_*.md` |

## 关键口径决策

- **现货 vs 合约**：交易链路维持 Spot 不动；行情页 mark price/funding/OI 借 USDT-M **公共**端点
  （`adapter.get_futures_metrics`，不可用返 null）。被适配层隔离、可逆；整体迁合约需老板拍板。
- 手动下单/改 SLTP 权限暂 `require_admin`（P4 RBAC 后放宽 trader+）；LIMIT 手动单返回"暂不支持"。
- 权限矩阵在 `src/services/system/permissions.py`，`role_aliases: {"user": "trader"}` 过渡映射。
- **端点变更后必须重导 OpenAPI**：`cd backend && uv run python scripts/export_openapi.py`
  → 前端 `npm run gen:api`；每期落地通知前端删对应 MSW handler（B4 流程）。

## 已完成（续，2026-07-05 晚）

- **P2b**：`/ws/market` Binance WS 代理（250ms 节流/订阅扇出/断线重连，worklog 20260705_2100）
- **P3**：Pilot AI 对话（SSE 工具循环 + agent_pending_actions 表 + confirm 白名单双重校验）
- **联调缺口 #1-4/6/7** 全收口（guard_verdict/account history/orders 列表/持仓字段/catchup 类型/risk limits，#5 留 P6）
- **P4 全量**（worklog 20260705_2200）：settings 三分区（加密+脱敏+权限探测）/ RBAC 四角色
  （require_permission 端点守卫、trader 可下单 viewer 403、owner 保护、pending 批准）/
  2FA TOTP 二段式（pyotp，secret Fernet 加密，scope=2fa 票据）。基线 **668 passed + 2 skipped**，openapi 58 paths。

## 待做（按序）

1. **P5** lab（候选/影子执行调度/灰度自动回滚，handoff 3.5）
2. **P6** performance（summary/monthly/attribution 三接口 + 联调缺口#5 聚合指标，handoff 3.8）
3. 通知渠道 token settings 化 + notifier 接线；owner bootstrap 授予；agent 真流式
