# AlphaPilot 现代化交易软件 — 全栈改造设计

- 日期：2026-06-28
- 状态：设计已批准（路线图 + 节奏 + 图标方案已定），待逐期 spec→plan→实现
- 范围：前后端全栈，对标 `AlphaPilot Design System` 参考设计系统，把当前"单页堆叠控制台"升级为现代化 AI 自主交易软件
- 关联：[`docs/project.md`](../../project.md)（工程宪法）、`AlphaPilot Design System/`（参考设计系统与 web/mobile UI Kit）

---

## 1. 背景与目标

老板反馈：当前前端"太丑、太 AI 化、功能太 low"。诊断结论：

1. **三套互相打架的样式系统**并存——`src/styles/design-system.css`（专业交易终端令牌，但几乎没被用上）、`src/app/globals.css`（蓝紫渐变 + 背景发光球的"AI 落地页风"）、`src/app/page.module.css`（仪表盘又一套蓝绿硬编码色）。三种蓝、三种卡片 = 廉价拼凑感。
2. **典型"AI 生成"特征**：背景浮动发光球、紫→蓝→青渐变 logo/按钮、玻璃拟态、超大圆角 28px、大面积发光阴影、营销式 hero。
3. **功能单薄**：整个前端是一页 1060 行的 Dashboard 把 8 路数据堆在一起，没有参考 Kit 的左侧栏、AI 决策卡、权益曲线、订单簿、回测绩效、策略/风控页、审计+AI 日报等。

**目标**：以 `AlphaPilot Design System` 为唯一事实源，做一款"专业交易终端"风格（方向 A：近黑底 + 等宽数字 + 发丝线 + mint/rose/violet 三色克制 + 零渐变零发光）、**功能对标参考 web UI Kit** 的现代化 AI 交易软件。

**关键事实**：项目内 `src/styles/design-system.css` 就是参考目录 `colors_and_type.css` 的拷贝——令牌早已就位，只是没真正用起来。

---

## 2. 设计原则与设计系统单一化

### 2.1 视觉方向（方向 A · 专业交易终端）
- 背景近黑 `--ap-bg-0 #07090F`，**纯色、零渐变、零发光球**。
- 强调色收敛：`--ap-mint`（盈/涨/PASS）、`--ap-rose`（亏/跌/REJECT）、`--ap-violet`（仅 AI 产物）、`--ap-amber`（降级/警告）、`--ap-cyan`（信息）。**彻底删除 `globals.css` 的 `--accent #60a5fa` 蓝紫体系**。
- 涨跌色只用于真实数值正负，不作装饰；violet 只出现在 AI 产物上。
- 圆角克制：卡片 12–16px、按钮/输入 8–12px、Pill 999px。删掉 28px 巨圆角。
- 阴影平面化：默认 `--ap-shadow-1`；glow 仅用于状态时刻（AI 输出 violet 脉冲 / 熔断 rose 脉冲），不作装饰。
- 数字纪律：所有价格/盈亏/百分比/trace 用 `JetBrains Mono` + `tabular-nums`；百分比 2 位小数；盈亏带 `+ / −` 前缀。
- 文案纪律：严肃、克制、工程化；**禁用 emoji**（用 Lucide 图标或色点替代）；时间用 `HH:mm:ss` / `MM-DD HH:mm` 绝对时间。

### 2.2 令牌单一事实源
- `src/styles/design-system.css` = 唯一令牌源（`--ap-*`）。
- `globals.css` 仅保留 reset + 基于 `--ap-*` 的全局基础类；删除蓝紫 vars、`shellAmbient*` 发光球、渐变 body。
- `page.module.css` 的硬编码色随页面重做迁移到令牌（P1）。
- **不引入 Tailwind**；沿用项目现有 React + CSS Modules 模式（决策 D3）。

### 2.3 图标
- 引入 `lucide-react`（设计系统钦定，决策 D1），按需 tree-shaking。封装统一 `Icon` 用法。清除 UI 中残留 emoji（如 confirm 文案里的 ⚠️）。

### 2.4 字体
- 已在 `design-system.css` 通过 Google Fonts 引入 `Inter` + `JetBrains Mono` + `Noto Sans SC`，无需新增。

---

## 3. 信息架构（8 段，grounded 在真实后端）

参考 Kit 的 7 段裁剪/收口为 8 段；把 1060 行单页 Dashboard 按页拆开。每段标注真实支撑端点。

| 段 | 路由 | 内容 | 真实支撑端点 |
|---|---|---|---|
| 主控制台 Cockpit | `/` | AI 决策 hero 卡 + 账户权益卡 + 关键指标 + 持仓预览 + 右侧实时事件流 | health / account / positions / decisions / risk-events / kill-switch / WS / events/catchup |
| AI 决策流 | `/decisions` | 决策历史列表 + 已执行/已拦截过滤 + 决策卡渲染 | decisions?limit=200 |
| 持仓与订单 | `/positions` | 持仓详情表 + SL/TP 可视化轨道 + 写操作 + 订单簿(P3) | positions / close-position / close-all / tasks · `[P3]` orders |
| 交易与绩效 | `/performance` | 已平仓交易 + 日报指标卡 + 前端聚合月度 PnL/交易统计 · 回测曲线(P5) | trades / reports / reports/generate |
| 策略与风控 | `/strategy` | 硬风控阈值只读(4 项) + 策略评分卡 + 交易对管理 | config/runtime / strategy-scores / admin/symbols |
| 归因与审计 | `/insights` | 逐笔归因叙述 + 维度聚合 + 风控事件时间线 + 审计日志 | attribution(+summary) / risk-events / admin/audit-logs |
| 管理后台 | `/admin` | 用户管理 / Symbol 管理 / 审计日志（换皮，行为不变） | admin/users / admin/symbols / admin/audit-logs |
| 设置 | `/settings` | 运行时配置中心 + AUTO 引擎开关 | config/runtime / kill-switch / pause / resume / auth/me |

全局 shell：**左侧栏 240px**（品牌 + 账户权益摘要 + 8 段导航 + 引擎状态）+ **顶栏**（页面标题 + 风控状态胶囊 + AUTO 徽章 + 通知红点 + ⌘K 占位）。

> 路由改名：`/admin/currencies` → `/admin/symbols`（语义收口，带旧路由重定向，放 P2）。决策 D4。

---

## 4. 功能落差矩阵（三档边界）

### 4.1 现有真实接口即可落地（P0–P2）
左侧栏/顶栏 shell、账户权益摘要、AUTO 徽章、风控胶囊降级版（OK/HALTED 由 account.daily_pnl_pct + 未解除 risk-events 推断）、AI 决策基础卡(Stepper 简版)、已执行/已拦截近似过滤(按 is_fallback)、关键指标(交易数/胜率/回撤/平均持仓，前端聚合)、持仓表全字段、SL/TP 轨道、平仓/一键平仓/解除熔断写操作、月度 PnL 柱状图(前端聚合 trades)、交易统计键值表、策略评分卡、硬风控只读 4 项、交易对 CRUD、归因+审计、运行时配置中心、WS 实时事件流(切 lib/ws.ts catchup)、Lucide 图标、统一危险操作 Modal、组件库沉淀。

### 4.2 后端小改解锁（P3）
- **扩展 `GET /api/decisions`** 返回已存字段：`entry_price/stop_loss/take_profit/position_size_pct/entry_type/llm_provider/llm_model/latency_ms` + 关联 `trace_id` → 决策卡字段网格 + trace chip。
- **新增 `GET /api/orders`**（`?symbol&limit`）→ 订单簿（orders 表字段齐全，仅缺接口）。
- **新增 `GET /api/account/history`**（`?range`）→ 权益曲线 WSpark + 1D/1W/1M 区间（account_snapshots 逐条已存，仅缺时序查询）。
- （可选）**`GET /api/risk/state`** → 完整三态风控胶囊（OK/WARN/HALTED + 仓位%/日损%/当前 regime）。
- 均为读现有表，**预计无需 alembic 迁移**。

### 4.3 中/大工程（P4–P5）
- `[中]` `GET /api/decisions/{id}/guards`（8 守卫明细聚合）+ `/features`（factor_snapshots join）→ 解锁 Graph/Timeline 决策卡变体。
- `[中]` AI 日报自然语言叙述（先用 `attribution.narrative` 前端拼凑过渡，后接 LLM 生成文案字段）。
- `[大]` 回测/绩效引擎：策略 vs HODL 对比曲线、账户级 Sharpe/Sortino、盈亏比。
- `[大]` 策略启停开关：策略级 `enabled` 字段 + 受控策略集管理（需迁移）。

### 4.4 占位/mock（不臆造）
⌘K 命令面板（无搜索端点，先占位）、引擎延迟/uptime（无指标端点，不渲染）、硬风控的周亏熔断/最大相关度/R:R/价差上限（后端无字段，不渲染）、Tweaks 场景预览（前端内部 QA 模式注入 mock）。

> **红线**：参考 Kit 凡是后端无数据的功能，一律按矩阵走"配接口/占位/mock"，**严禁前端编造数据**；占位处给明确空态，不显示假数字。

---

## 5. 分期路线图（P0→P5 顺序走到底，已批准）

每期独立可上线，结束前 `next build` + `tsc --noEmit` + `vitest`（前端）+ `pytest`（涉及后端期）+ `ruff`（后端期）全绿才提交并推送。

### Phase 0 · 地基（纯前端，零行为改动）
统一 `--ap-*` 令牌为唯一源；引入 lucide-react + 清 emoji；沉淀组件库；左侧栏 shell + 顶栏替换现有窄顶栏；危险操作统一 Modal 基础设施；事件总线 Provider（lib/ws.ts catchup）基础设施。**详见 §6。**

### Phase 1 · 拆页 + 主控制台重做（纯前端，现有接口）
把 1060 行单页拆成 8 段路由骨架；主控制台 = AI 决策 hero 卡(Stepper 基础版) + 权益卡 + 关键指标(前端聚合) + 持仓预览 + 实时事件流。**逐个保住高危写操作契约（close-all 异步入队 + task 轮询、CLOSE ALL 口令、mainnet 二次确认、解除熔断）+ admin 边界 + 补前端单测。**

### Phase 2 · 能力页铺满（纯前端，现有接口）
决策流 / 持仓与订单(SL/TP 轨道) / 交易与绩效(trades+reports+前端聚合) / 策略与风控(评分+硬风控4项+symbols) / 归因与审计 / 设置(运行时配置+AUTO) / 管理后台三页换皮；`/admin/currencies → /admin/symbols` 改名 + 重定向。

### Phase 3 · 后端三小改解锁视觉亮点（后端 + 前端）
扩展 `/api/decisions` 字段；新增 `GET /api/orders`、`GET /api/account/history`；（可选）`GET /api/risk/state`。前端接入：决策卡字段网格+trace、订单簿、权益曲线、完整风控胶囊。补后端测试。

### Phase 4 · AI 决策深度可视化（中工程）
`GET /api/decisions/{id}/guards` + `/features` → 解锁 Graph/Timeline 决策卡变体；AI 日报叙述（attribution.narrative 过渡 → LLM 文案）。

### Phase 5 · 绩效/回测引擎 + 策略启停（大工程）
回测 vs HODL / 账户级 Sharpe·Sortino / 盈亏比；策略级 enabled 开关（含 alembic 迁移）。

---

## 6. Phase 0 详细设计（首个子项目，足够开工）

### 6.1 交付物
1. **令牌单一化**
   - `design-system.css`：保持唯一令牌源；`body` 背景改纯 `--ap-bg-0`（去渐变）。
   - `globals.css`：删除 `--accent/--accent-2`、`shellAmbient*`、渐变 body、玻璃拟态发光；保留的 auth/admin 类暂时把硬编码色改吃 `--ap-*`（避免塌陷，整页重做在 P2）。
   - `layout.tsx`：移除两个 `shellAmbient` 发光球 div。
2. **lucide-react** 依赖引入（`cd frontend && npm install lucide-react`，提交 lock）；封装 `Icon`；清除 UI emoji。
3. **组件库** `src/components/ui/`（React + CSS Modules + `--ap-*`）：`Button`、`Card`、`StatCard`、`Badge`(Pill)、`Table`(含表头 uppercase/数字列右对齐 mono)、`RiskBanner`、`Modal`、`Dot`、`Sparkline`(基础)。各组件附最小 vitest（渲染/语义）。
4. **新 shell** 替换现有 `app-shell.tsx`：`Sidebar`(240px：品牌 + 账户权益摘要 from account + 8 段导航 + 活跃指示条 + 引擎状态 from kill-switch) + `Topbar`(页面标题 + 风控胶囊降级版 + AUTO 徽章 from kill-switch/pause/resume + 通知红点 from 未解除 risk-events + ⌘K 占位)。响应式：窄屏侧栏折叠/抽屉。
5. **危险操作 Modal**（替换 `confirm/alert/prompt`）作为基础设施（dashboard 实际接入在 P1，避免提前动写路径）。
6. **事件总线 Provider**（基于 `lib/ws.ts` EventBusClient + `/api/events/catchup`）作为基础设施（页面消费在 P1+）。

### 6.2 验收标准
- `cd frontend && npm run build` + `npx tsc --noEmit` + `npm test`(vitest) 全绿。
- 现有所有路由（/、/login、/register、/admin/*）在新 shell 下**功能与行为不变**；admin 权限边界（RouteGuard + viewer 只读降级）不变。
- 全站无 `--accent` 蓝紫残留、无发光球、无渐变 body；数字 mono 化。
- 后端零改动。

### 6.3 P0 不做
不拆 dashboard 单页、不改任何写操作行为、不动后端、不重做 auth/admin 页内部（仅令牌换色防塌陷）。

---

## 7. 红线与风险

1. **写操作回归（最高危）**：1060 行 Dashboard 聚合 8 路数据 + 高危写操作。拆页/换皮必须逐个保住 close-all 异步入队+task 轮询、CLOSE ALL 口令、mainnet 二次确认、解除熔断的交互契约，并补前端单测。
2. **admin 权限边界**：runtime-config/kill-switch/tasks/symbols/users/audit-logs/commands 为 admin-only，普通用户 403。换皮后保留 RouteGuard 与 viewer 只读降级，不把 admin 数据渲染给普通用户。
3. **WS 迁移**：从内联裸 WebSocket 切到 `lib/ws.ts` EventBusClient + catchup，需正确处理 basePath 推导(`/ap-dev/ws`)、event_id 去重、断线回放。
4. **不臆造数据红线**：见 §4.4。
5. **三套 CSS 令牌迁移**：组件吃的是全局/module 类名而非令牌，直接删会大面积塌陷——**逐组件迁移、小步提交**，非一刀切。
6. **响应式重构**：双份 DOM（桌面表/移动卡）散落、断点不统一(768/600/960)。先沉淀 Table/Card 组件再逐页替换。
7. **路由改名**：`/admin/currencies → /admin/symbols` 需旧链接重定向，避免书签失效。

---

## 8. 测试与验收基线

- 当前基线：后端 526 passed + 2 skipped；前端 vitest 绿；`next build` + `tsc --noEmit` 通过；ruff 0 警告。
- 每期：上述命令全绿才提交推送；涉及后端的期补 pytest（schema/controller）。
- 前端写操作契约：补/保 Vitest 覆盖（api envelope、auth 会话、写操作确认流）。

---

## 9. 决策记录

- **D1**：图标用 `lucide-react`（设计系统钦定）。
- **D2**：节奏 P0→P5 顺序走到底。
- **D3**：样式实现 = React + CSS Modules + `--ap-*` 令牌；**不引入 Tailwind**。
- **D4**：`/admin/currencies → /admin/symbols` 改名 + 重定向（P2）。
- **D5**：不臆造数据红线（后端无数据 → 配接口/占位/mock）。
- **D6**：信息架构定为 8 段（见 §3）。
