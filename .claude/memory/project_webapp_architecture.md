# webapp 前端架构决策（2026-07-05 老板批准，前后端都要遵守）

**权威文档：[`docs/webapp前端架构.md`](../../docs/webapp前端架构.md)** —— 目标形态、四步升级路线（S1-S4）、后端配合清单（B1-B4）、部署形态全在里面。

## 一句话结论

`webapp/`（Vite SPA）确定为**唯一前端主线**；Next.js `frontend/` 冻结退役（S4 后归档）。
数据层升级为：OpenAPI 生成类型 + TanStack Query + WS 直写 Query 缓存 + MSW 网络层 mock +
httpOnly cookie 认证 + build-once 部署。

## 对后端会话的要求（做 handoff 后端实现时必看）

按 `docs/webapp前端架构.md` §3 执行，优先级：

1. **B1 OpenAPI 契约固化**：export_openapi 脚本 + 路由显式 `operation_id` + 统一响应包的
   `data` 字段必须有具体 Pydantic 模型（`dict[str, Any]` 生成 unknown 等于没契约）
2. **B2 WS 事件补齐**：`risk.state` 快照事件（或 `GET /api/risk/state`）、`account.snapshot`
   权益快照事件；信封沿用现有 `EventEnvelope` 不改；`market.{symbol}` 在 P2 计划内
3. **B3 认证升级**：login 支持 httpOnly cookie 下发（与 Bearer 并存）、logout、
   `GET /api/admin/roles` 权限矩阵下发
4. 新端点落地时通知前端删对应 MSW handler + 重新生成 OpenAPI 类型即可，前端业务代码零改动

## 对前端会话的要求

- UI 层不动（token 纪律照旧）；升级按 S1→S4 顺序，每步独立提交可回退
- 业务代码只允许一条真实 fetch 路径；mock 一律进 MSW handler，禁止在 service 里写 if(USE_MOCK)
- WS 按 `event_type` 分发、`event_id` 去重、断线带 `since` 走 catchup
