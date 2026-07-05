# webapp 前端架构 · 目标形态与前后端对接契约

> 状态：**已定稿（2026-07-05 老板批准）**。本文档是 `webapp/` 后续演进的权威依据，
> 也是后端配合调整的需求清单。前端升级过程见 `docs/worklog/`。
> 前置背景：`webapp/`（Vite SPA）已按设计交接包全量落地 11 页 + 实时层，
> 与 Next.js `frontend/` 并存；本方案确定 webapp 为唯一前端主线，`frontend/` 冻结退役。

## 1. 结论（从零推导的最佳形态）

产品本质：**认证后才可见、强实时、单租户的内部交易控制台**。据此每层最优解：

| 层 | 方案 | 理由 |
|----|------|------|
| 应用形态 | Vite SPA + React 18 + TS strict + Tailwind（token 映射） | 无 SEO/SSR 需求；SPA 部署回滚最简 |
| REST 类型 | **OpenAPI 自动生成 TS 类型/客户端**（FastAPI 免费产出 schema） | 契约漂移在 CI 编译期报错，不进运行时 |
| 服务端状态 | **TanStack Query** 统一缓存 | 缓存/重取/去重/loading 一次解决 |
| 实时 | 单条 WS → zod 校验 → **直接 patch/invalidate Query 缓存** | REST 与 WS 汇成一个状态模型；断线重连自动 refetch |
| mock | **MSW 网络层拦截**（dev + test 共用同一套 handler） | 业务代码只有一条真实 fetch 路径；后端就绪删 handler 即可 |
| 认证 | JWT **httpOnly cookie** + 路由守卫 + `usePermission()` | token 不落 localStorage（防 XSS）；权限矩阵由后端下发，前端不留第二份真相 |
| 测试 | vitest+RTL（组件）/ MSW（集成）/ Playwright（3 条关键路径） | 关键路径：登录、HALTED 五件套、下单预检**拒绝路径** |
| 图表 | lightweight-charts（已落地） | — |
| 交付 | **build once, deploy many**：单一 dist + nginx 容器 + 运行时 config 注入 | uat 验过的工件与 prod 字节一致 |

UI 层（11 页、`--ap-*` token 纪律、决策卡三变体、K线）**原样保留**，升级集中在数据层与工程化。

## 2. 前端升级路线（分四步，每步独立可验收/可回退）

| 步骤 | 内容 | 验收 |
|------|------|------|
| **S1 mock 换 MSW + OpenAPI 类型** | `msw` handler 承接现 mock 数据；`services.ts` 删 USE_MOCK 双实现只留 fetch；后端已就绪端点用 openapi 生成类型（`src/api/generated/`），未就绪域保留手写类型逐步收敛 | build 全绿；dev 无后端时页面数据不变 |
| **S2 TanStack Query + WS 管道** | 页面数据全部 `useQuery`；`stream.ts` 出口从"各页 setState"改为写 Query 缓存（`setQueryData`/`invalidateQueries`）；WS 消息适配后端 `EventEnvelope`（按 `event_type` 分发、`event_id` 去重、断线用 `since` 补偿） | 实时行为与现状等价；断线重连自动 refetch |
| **S3 认证闭环** | 登录调真实 `/api/auth/login`（mock 下 MSW 兜）；RequireAuth 路由守卫；`usePermission()` 读 `/api/admin/roles`；401 统一跳登录 | viewer 角色看不到写操作入口；未登录访问任意页重定向 |
| **S4 测试 + 交付管线** | vitest+RTL 基线、Playwright 3 条关键路径；`webapp/Dockerfile`（nginx + 运行时 `config.js` 注入）+ compose 接入 + deploy 脚本；`frontend/` 冻结归档 | 三环境同一工件晋级；CI 全绿 |

## 3. 后端配合清单（按优先级）

> 后端会话开工前必读本节。已有两份实现计划在 `docs/superpowers/plans/`
> （P1 决策流式 ✅ 已完成、P2 行情+手动下单 进行中），以下是**增量调整项**。

### B1 · OpenAPI 契约固化（S1 依赖，工作量小）

- 提供 schema 导出脚本（建议 `backend/scripts/export_openapi.py`：
  `from src.app import app; json.dump(app.openapi(), ...)` → `docs/api/openapi.json`）
- 路由统一显式 `operation_id`（FastAPI 默认生成的名字又长又不稳，前端生成的函数名会跟着变）
- 响应模型显式化：统一响应包 `{code, success, message, data}` 的 `data` 必须有具体
  Pydantic 模型（`dict[str, Any]` 会生成 `unknown`，等于没有类型）

### B2 · WS 事件面补齐（S2 依赖）

前端按现有 `EventEnvelope`（`event_id/event_type/payload/...`）适配，**信封不用改**。需补：

- `risk.state`：风控状态快照事件（`{state: OK|WARN|HALTED, day_loss_pct, positions_pct, regime}`），
  状态迁移时发布；或提供 `GET /api/risk/state` 由前端在收到
  `circuit_breaker.triggered`/`risk.event.triggered` 后主动拉
- `account.snapshot`：账户权益快照事件（account_state 同步后发布），驱动权益曲线实时生长
- `market.{symbol}` 代理转发（P2 计划已含，节流 ≥250ms）
- 前端会把**所有** envelope 事件映射进事件流 UI，事件类型无需为前端专门归并

### B3 · 认证升级（S3 依赖）

- `/api/auth/login` 支持 **Set-Cookie（httpOnly + SameSite=Lax + Secure）** 下发 JWT，
  与现有 Bearer 头并存（不破坏已有调用方）；鉴权依赖项增加 cookie 读取回退
- `POST /api/auth/logout`（清 cookie）
- `GET /api/admin/roles` 权限矩阵下发（handoff/03 §3.7 已规划）——前端 `usePermission()` 的唯一数据源

### B4 · 后续（随 handoff 各期推进，无前端阻塞）

- settings（3.6）/ agent SSE（3.4）/ lab（3.5）/ performance（3.8）端点落地时，
  前端只需在 MSW 里**删对应 handler** + 重新生成 OpenAPI 类型

## 4. 部署形态（S4）

```
webapp/Dockerfile:  npm ci && npm run build → nginx:alpine
  ├─ /usr/share/nginx/html      # dist（同一工件晋级三环境）
  ├─ /api /ws → 反代 backend    # nginx.conf
  └─ entrypoint: 由环境变量渲染 /config.js（window.__AP_CONFIG__），前端启动时读取
```

- dev/uat/prod 的差异只在容器环境变量，不重新 build
- `frontend/`（Next.js）：S4 完成并稳定一个迭代后打 tag 归档、移出 compose 与 CI；
  期间保持可部署状态作回退

## 5. 决策记录

- **为何不继续 Next.js 线**：认证后控制台无 SSR 收益；UI 完成度已被 webapp 反超；
  双线维护每个页面改动付双倍成本（决策于 2026-07-05，老板批准）
- **为何 MSW 而非 services 双实现**：双实现意味着业务代码里永远有两条路径要维护，
  且 mock 无法复用到测试；MSW 在网络层拦截，业务代码与生产完全一致
- **为何 build-once 而非按环境 build**：uat 验证过的工件与 prod 字节一致，
  排除"构建期差异"这一整类事故
