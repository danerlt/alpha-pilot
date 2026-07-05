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

## 待做（按序）

0. **联调缺口收口（小项，优先插队）**：前端已对真后端跑通浏览器级联调（2026-07-05），
   发现 7 个契约缺口，清单+复现环境见 **[`docs/webapp联调-后端待办.md`](../../docs/webapp联调-后端待办.md)**
   —— 高优先三项：DecisionRead 补守卫裁决字段 / GET /api/account/history / GET /api/orders 列表
1. **P2b**：`market.{symbol}` WS 行情代理（盘口/逐笔 Binance WS 转发、节流 ≥250ms、不落库）
2. **P3**：Pilot AI 对话（agent 域 SSE + 工具白名单 + pending action confirm，handoff 3.4）
3. **P4**：settings 三组接口 + RBAC（owner/admin/trader/viewer 落 user 表）+ 2FA（handoff 3.6/3.7）
4. **P5** lab / **P6** performance
