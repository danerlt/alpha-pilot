# 实施计划：webapp 产品审查变动落地（18 工作包 + 后端还原）（2026-07-08）

> 本文件为 change-planner 依据 `docs/product-review/webapp变动交接清单.md`（权威） + `docs/product-review/webapp产品审查报告.md`（行号出处） + `docs/project.md`（工程宪法）拆解的可执行计划。
> **本计划已整份覆盖并作废旧的「前端现代化 P0→P5」计划**（那份 P0/P1 标完成的内容已过时、与本批变动无关，不再保留）。
> 交付对象：`frontend-dev` / `backend-dev` 两个 agent 直接领取。每完成一块即按 CLAUDE.md 提交并 push。

---

## 概览

- **来源**：webapp 全量产品审查（`product-advisor`，2026-07-08 实跑 mock）→ change-reviewer 逐条评审 + 行号核实 → 老板 2026-07-08 五条复核。
- **总条目**：18 个工作包（WP1–WP18）。裁决全部为「采纳 / 修改后采纳」，暂缓/否决项见交接清单末尾，不进本计划。
- **端别分布**：纯前端 WP = 11 个（WP3/WP4/WP6/WP7/WP8/WP9/WP10/WP11/WP12/WP17/WP18，其中 WP10/WP18 含移动端）；两端 WP = 6 个（WP1/WP2/WP5/WP13/WP14/WP15）；前端+mock/后端 = 1 个（WP16）。
- **老板五条复核（已全部落实到下方任务）**：
  1. WP1 急停一步到位 → 后端**原子急停端点**（closeAll+pause 单事务/明确回执），前端显分步结果，**不做 try/catch 过渡方案**。作为阶段三首交付。
  2. WP4 假安全控件只做「去误导 + 诚实文案」，**不放行运行期改熔断阈值 / 真实 RBAC**（留 V0.2）。
  3. 注册入口改「请联系管理员开号」，**不接已按 C5 禁用的 `/api/auth/register`**。
  4. 【新增 WP18】整站响应式 shell 提级，原 F 类暂缓项全部纳入。
  5. 纯前端批次先行（阶段一/二），依赖后端的编入阶段三并标清所需接口。

### 阶段划分与总体依赖图（文字描述）

- **阶段一（纯前端 · 信任锚点与资金安全）**：WP3 → WP4 → WP6 → WP7 → WP9 → WP2(前端连接态部分)。可完全独立交付，无后端依赖。其中 WP7 依赖 WP8 的 `ConfirmDialog`/`Modal` 已存在（现成组件，见下），守卫中文字典为 WP7/WP5/WP13 共享，先落地。
- **阶段二（纯前端 · 无障碍/响应式/本地化/绩效/体验收尾）**：WP8（focus trap 一改全站受益，优先）→ WP10 → WP11 → WP12 → WP17 → WP18。与阶段一可部分并行（不同文件），但 WP8 的 Modal focus trap 建议先于阶段一 WP7 的确认弹窗落地以复用。
- **阶段三（依赖后端 · 端点先行）**：WP1(后端原子急停，**首交付**) → WP5(后端透传 + 前端联调) / WP13(后端拒绝端点 + 前端) / WP14(后端撤单端点 + 前端) / WP15(后端历史查询 + 前端) / WP16(mock/后端校验 + 前端) / WP2(后端调度心跳) + 后端还原盘点新缺口 N1/N2/N3。后端端点为对应前端任务的**前置**。

### 后端还原盘点结论（去重后）

对照 `webapp/src/api/services.ts` 实际调用与 `backend/src/controllers/api/v1/**` 已实现端点，逐条核对结果：

- **绝大多数端点后端已真实落地**（前端先行/后端还原此前已完成）：`/api/decisions/{id}` 详情端点已存在（`decisions.py:61`，含 features + guard_events）；审计端点 `/api/admin/audit-logs` 已透出 `before_json/after_json/resource_id`（`admin.py:290`）；`/api/account/history` 权益序列已存在（`account.py:44`，services.ts:98 注释为**过时**）；lab promote 已服务端门槛校验（`lab.py:86`）；`/api/admin/roles` 权限矩阵已下发（`admin.py:299`）。故这些**不作为缺口**。
- **已被 WP 覆盖的后端项**（不重复列）：原子急停(WP1)、审计 before/after 写入填充与 Agent pending 前后值(WP5)、拒绝 pending 用户端点(WP13)、撤单端点(WP14)、审计按时段查询(WP15)。
- **新缺口（本盘点新增，未被上述 WP 覆盖）共 3 项**，并入阶段三：
  - **N1 · 调度器真实心跳**（WP2 后端依赖）：`/api/health`（`health.py:22`）只返回 status/trading_mode/version/runtime_credentials，**不反映调度进程存活**，侧栏「引擎运行中·48ms」要真值需后端补心跳。
  - **N2 · 通知渠道「已绑定」标志**（WP17 依赖）：`NotificationSettingsOut`（`schemas/settings.py:70`）只有 `channels: dict[str,bool]`（开关）与 `subscriptions`，**无 per-channel 是否已配置凭据的标志**，WP17「未绑定禁用开关」要真值需后端补 `channels_configured`。
  - **N3 · 用户「最近活跃」字段**（WP13 10f 依赖）：`User` 无 `last_login_at`/最近活跃字段，`wire.ts:580` 恒显「—」。**建议暂缓 / V0.2**（WP13 已决定先隐藏，非阻塞；还原需 alembic 迁移加字段 + 登录时更新）。

---

## 阶段一: 纯前端 · 信任锚点与资金安全

**目标**：一次性消除「假控件 / 假数据 / 合约概念混入 / 熔断阈值自相矛盾 / 下单无确认 / 强制动画藏结论」这些直接触及信任与资金安全底线的前端病灶。全部纯前端、无后端依赖，可最先交付。
**成功标准**：webapp `npm run build` + `tsc --noEmit` 通过；preview（5173 mock）下：AUTO 接真实 pause/resume 态、权限矩阵/交易对「添加」不再假可点、熔断阈值全站读同一真值、行情/下单无任何合约概念、手动下单必弹二次确认、决策卡三变体都显 SL/TP、进页不再强制重放动画。设计系统纪律（`--ap-*` token、JetBrains Mono、violet 仅 AI、涨跌色仅真实正负、无 emoji、lucide 图标）零破坏。
**测试**：`npm run build`、`tsc --noEmit`、`webapp/src/api/services.test.ts` 保持绿；preview 人工验证每条验收；如触及 wire 映射函数补 vitest 单测。
**状态**：未开始

### 任务 1.1　WP3　[纯前端]
- **变动来源**：主控台/熔断横幅 · P1 · 熔断阈值文案硬编码且自相矛盾（HaltBanner −2.00% vs 全站 3% vs 磁贴 −8%）。
- **改动点**：`webapp/src/components/**/HaltBanner.tsx:48-49`（写死「≥ 阈值 −2.00%」「距阈值以 -2.0 计算」）、`webapp/src/pages/Dashboard.tsx:163`（磁贴写死「阈值 −8%」）。均改读 `strategyApi.hardLimits()` → `/api/risk/limits` 真值（`fromWireRiskLimits`，services.ts:187）。
- **改成什么**：HaltBanner 阈值文案 + WARN「距阈值」计算、Dashboard 磁贴阈值全部取 `risk/limits` 返回的日亏损限额（`MAX_DAILY_LOSS_PCT`），单一数据源，无魔数。
- **验收标准**：preview 下横幅与磁贴显示的熔断阈值与 `/api/risk/limits` 返回值一致（mock 下为 3%）；全站不再出现 −2.00% / −8% 硬编码。
- **测试**：`build` + `tsc`；grep 确认源码无 `-2.00`/`-8`/`2.0` 魔数残留；preview 目视三处一致。
- **风险与注意**：熔断线是信任锚点，务必确认 `risk/limits` 字段单位（百分比 vs 小数）与展示格式化一致，避免 0.03 显成 0.03% 的新错。无需 Alembic / openapi 重导。

### 任务 1.2　WP4　[纯前端]
- **变动来源**：后台/风控/顶栏 · P1 · 假安全控件去误导（老板复核：只做「去假可点 + 诚实文案」，不放行真改）。
- **改动点**：
  - `webapp/src/pages/Admin.tsx:387-395` 权限矩阵格：去 `cursor-pointer`/mint hover，标注「固定角色模型，不可自定义（10a）」。
  - `webapp/src/pages/Risk.tsx:74-76` 硬风控警示条文案改「硬风控阈值仅由部署配置调整，运行期不可变更（7a）」，去掉「修改需 admin 权限并记录审计」这类暗示可改的措辞。
  - `webapp/src/components/**/Topbar.tsx:82` AUTO：静态 `<div>` 改为接真实 `commandsApi.pause/resume` 态显示（引擎运行中/已暂停），点击走 `ConfirmDialog` 口令确认（2a）。
  - 通知铃铛（`Topbar.tsx:73`）：去写死红点，补 `aria-label`（无真实未读数则不显红点）。
  - `webapp/src/pages/Risk.tsx:119` 交易对「添加」按钮：无真实表单则置灰 + 标「即将支持（7b）」；ON/OFF 若无启停端点则保持只读且不做成假开关样式。
- **改成什么**：所有「看起来能点/能改实则无功能」的控件，要么接真值（AUTO 接 pause/resume），要么诚实置灰/改文案；**不新增运行期改熔断阈值、不做真实 RBAC 授权/撤销**（V0.2）。
- **验收标准**：preview 下权限矩阵格无手型光标/无 hover 高亮且有「固定角色」说明；Risk 硬风控文案为「运行期不可变更」；AUTO 反映真实引擎态且点击弹口令确认；铃铛无假红点且有 aria-label；交易对「添加」置灰带说明。
- **测试**：`build` + `tsc`；preview 逐项目视；AUTO 点击流程走 ConfirmDialog（复用现成组件，见任务 2.1 说明）。
- **风险与注意**：AUTO 接 pause/resume 属真实控制动作，务必 `ConfirmDialog` 口令确认 + 成功/失败反馈，勿静默。严禁越界做真 RBAC / 改阈值。无 Alembic / openapi。

### 任务 1.3　WP6　[纯前端]
- **变动来源**：行情/持仓/实验室 · P1 · 现货去合约概念 + 下单做多化（与「V0.1 仅现货做多」定位直接矛盾）。
- **改动点**：
  - `webapp/src/pages/Market.tsx:232-238`、`:275-301`：去掉资金费率/持仓量 OI/标记价/指数价/下次结算，换现货字段（24h 成交额 / 买一卖一 / 价差 / 成交笔数）（3a）。
  - `webapp/src/components/**/OrderTicket.tsx:104`：去掉「做空 / SELL」方向，SELL 改「卖出(平仓)」并绑 `reduce_only`（3b）；V0.1 亦可只留买入侧。
  - `webapp/src/components/**/PositionsTable.tsx:79`：去掉 `side === "LONG" ? "mint" : "rose"` 的 rose 做空死分支，固定 LONG 呈现（M10b）。
  - Lab 候选（`webapp/src/api/mock/data.ts:429`）：把「资金费率过滤」换成现货有意义候选（成交量 / 波动率 / 价差过滤）（8b）。
- **改成什么**：全站不出现任何永续/合约概念；下单只表达现货做多 + 平仓（reduce-only）。
- **验收标准**：preview 行情页无合约字段；下单面板无「做空」，SELL 显示「卖出(平仓)」；PositionsTable 无 rose 做空分支；Lab 候选无资金费率项。
- **测试**：`build` + `tsc`；preview 目视；grep 确认无 `资金费率`/`OI`/`标记价`/`做空`/`SELL` 误导文案残留（保留必要的 reduce-only 语义）。
- **风险与注意**：SELL 改语义后须确认下单 payload `reduceOnly` 正确传递（services.ts:85 `reduce_only`），避免把平仓当反向开仓。mock data.ts 属前端 mock，改动不影响真后端。无 Alembic / openapi。

### 任务 1.4　WP7　[纯前端]
- **变动来源**：行情/持仓 · P1 · 手动下单二次确认 + 守卫中文字典（真实下单无确认 + 机器串看不懂）。
- **改动点**：
  - `webapp/src/components/**/OrderTicket.tsx:86-95`：提交前弹 `ConfirmDialog`（现成组件，见任务 2.1）显摘要（方向/数量/名义/SL/TP/预检结论），确认后才 `ordersApi.place`（3c）。
  - 守卫预检渲染 `OrderTicket.tsx:227-228`（`c.check` / `c.note`）与持仓编辑弹窗 `Positions.tsx:225`：套用**审查报告附录 A 守卫中文字典**——左标签走字典、右侧通过态显「达标值(限额)」、拦截态显红字一句话中文原因、原始机器串收进 `title` tooltip（G 类 / 5b）。字典建议新建 `webapp/src/lib/guardDict.ts`，与后端 guard key 对齐（`kill_switch/daily_loss/consecutive_losses/balance/duplicate_position/position_size/single_risk/sl_distance/rr_ratio/chaotic_regime/review/strategy_enabled`）。
  - `OrderTicket.tsx:155`：修正仓位% 公式 `*0.1` bug——点「100%」应下满仓名义而非 ~10%（3e）。
- **改成什么**：任何真实下单前必有二次确认摘要；守卫项对用户显示中文人话，机器串仅进 tooltip；仓位百分比按钮语义与计算自洽。
- **验收标准**：preview 点「买入 BTC」先弹确认摘要，取消不下单；守卫项显示中文标签（如 `sl_distance` → 「止损距离」）而非英文 key；点 100% 名义与满仓一致。
- **测试**：`build` + `tsc`；`guardDict.ts` 补 vitest 单测（key → 中文标签映射、缺失 key 回退原串）；preview 走一遍下单确认流。
- **风险与注意**：守卫字典 key 必须与后端实际 check key 完全一致（附录 A 已列），漏一个 key 要回退显示原串而非崩溃。字典为 WP5/WP13 共享，先落地。无 Alembic / openapi。

### 任务 1.5　WP9　[纯前端]
- **变动来源**：主控台/决策流/决策卡 · P1 · 强制动画只播一次 + 决策卡保留 SL/TP。
- **改动点**：
  - `webapp/src/components/**/StreamingDecision.tsx:54-62`：动画只对**新到达的实时决策**播一次（由 WS `decision.complete` 触发），刷新/返回/换 symbol 直接展开完整卡，保留手动「重放」按钮（M6a）。
  - `webapp/src/components/**/DecisionCard.tsx:88`：Stepper/Timeline/Graph 三变体**均保留** SL/TP/入场/仓位（作通用头部/摘要条），变体只改「决策过程」可视化形态（M5a）。
  - Graph 变体：移为「深看单条」详情视图（`min-w-960px` 横向滚动场景），页头样式切换器移到设置页或移除（4c/M5b）。
- **改成什么**：进入监控页即刻见最新决策结论与 SL/TP，不被 ~3.9s 动画阻塞；换卡片样式不再藏掉止损止盈。
- **验收标准**：preview 刷新主控台，hero/决策流首条直接展开（无强制重放）；切到 Timeline/Graph 变体后 SL/TP/入场/仓位仍在；页头不再有调试向样式切换器（或已移设置页）。
- **测试**：`build` + `tsc`；preview 目视三变体均含价位磁贴；验证「重放」按钮仍可手动触发动画。
- **风险与注意**：变体存 localStorage，改造后须保证历史 localStorage 值不导致三变体缺字段。动画「只播一次」的判定条件（新 `decision.id` 且来自实时事件）要与 catchup/刷新路径区分。无 Alembic / openapi。

### 任务 1.6　WP2（前端连接态部分）　[前端]
- **变动来源**：侧栏/事件流/主控台 · P1 · 全站连接态/数据新鲜度 + 侧栏引擎状态 + LIVE（「看似实时其实冻结」比断线更危险）。
- **改动点**：
  - `webapp/src/api/stream.ts`（WsStream）：暴露 `connected` / `reconnecting` 状态给 UI（现已有指数退避重连 + `event_id` 去重 + `since` 回放，仅需把内部状态提升为可订阅）。
  - `webapp/src/pages/Dashboard.tsx:200`：事件流标题「LIVE」静态 Pill 改为据连接态渲染：已连→LIVE(mint)、重连中→「重连中…」(amber)、断开→「已断开」(rose) + 最后更新时间（M11a）。
  - `webapp/src/components/**/Sidebar.tsx:115-116` / `:119-121`：「引擎运行中·48ms」写死值改为**同源**连接态（M1b，与 Dashboard 合并同一数据源）；延迟位先接前端可得的 WS RTT，**引擎真实存活**留任务 3.8（WP2 后端心跳 N1）接入后替换。
- **改成什么**：前端从 WsStream 连接态驱动全站新鲜度指示，断线立刻显「已断开/重连中」而非恒亮 LIVE。
- **验收标准**：preview 下断开 mock WS（或模拟）时，LIVE 变「重连中…/已断开」并显最后更新时间；侧栏引擎状态与主控台同源不打架。
- **测试**：`build` + `tsc`；preview 手动断连观察状态切换；WsStream 状态暴露如抽成 hook 补 vitest。
- **风险与注意**：本任务只做「连接态」真值；侧栏「引擎（调度器）真实存活 + 真实 RTT」依赖后端 N1（任务 3.8），在其交付前侧栏延迟位可先标「—」而非假 48ms，避免制造新的虚假安心。无 Alembic / openapi。

> **说明（现成组件复用，全阶段通用）**：`ConfirmDialog`（含 `requireText` 口令、danger 变体）、`Modal`（Esc+背景关闭+`role=dialog`）、`MaskedInput`、`Switch`、`SparkLive` 均已存在（审查报告 M9/M10 已确认）。所有新增确认/弹窗/脱敏输入**一律复用，禁止新建**。

---

## 阶段二: 纯前端 · 无障碍 / 响应式 / 本地化 / 绩效 / 体验收尾

**目标**：补齐系统性可访问性缺口（一处 focus trap 全站弹窗受益）、整站响应式 shell（移动端看盘+操作）、时区本地化、绩效页正确性与零散体验收尾。全部纯前端。
**成功标准**：`npm run build` + `tsc --noEmit` 通过；危险弹窗键盘 Tab 焦点锁在对话框内、关闭归还焦点；375/768/1180 宽下 shell 不横向溢出、风控胶囊常驻、可看盘可操作；审计/事件流时间与后台管理日志本地时区一致；Performance 净收益磁贴颜色随真实正负；2FA 显二维码、通知未绑定渠道禁用开关。
**测试**：`build` + `tsc`；preview 多断点（375/768/1180/桌面）目视 + 键盘 Tab 走查危险弹窗；触及格式化/映射函数补 vitest。
**状态**：未开始

### 任务 2.1　WP8　[纯前端]（建议最先做，一改全站受益）
- **变动来源**：弹窗/表单原子 · P1 · Modal/ChatDrawer focus trap + 表单 label + ARIA。
- **改动点**：
  - `webapp/src/components/ui/Modal.tsx`：加 focus trap（打开聚焦首个可聚焦元素、循环 Tab、关闭归还触发焦点）——`ConfirmDialog`/编辑SLTP/平仓/切主网/急停弹窗全部继承（M9a）。
  - `webapp/src/components/**/ChatDrawer.tsx:151-157`：复用 Modal 的 Esc 监听 + focus trap，打开聚焦输入、关闭归还焦点（M4a）。
  - `webapp/src/components/ui/form.tsx:16-20`：`Field` label 由纯 `<div>` 改 `<label htmlFor>` 关联 input/select（M9b）。
  - 命令面板 `CommandPalette.tsx`（容器加 `role="dialog"`、输入 `aria-label`）+ 图表容器补 `role="img"`/`aria-label`（M3c，深度无障碍留 V0.2）。
- **改成什么**：所有危险弹窗键盘焦点不逃逸到背景、可 Esc 关闭并归还焦点；表单字段读屏可念、点 label 聚焦。
- **验收标准**：preview 打开平仓/切主网/急停等弹窗，Tab 循环停在弹窗内，Esc 关闭后焦点回到触发按钮；点字段 label 聚焦对应输入；ChatDrawer 可 Esc 关闭。
- **测试**：`build` + `tsc`；键盘 Tab 走查各弹窗；如抽 focus-trap hook 补 vitest（首/尾元素循环）。
- **风险与注意**：Modal 是全站弹窗基座，改动影响面大，须回归所有复用点（平仓/编辑SLTP/切主网/急停/ConfirmDialog/EditUser）。含资金安全操作的弹窗焦点逃逸=可能误触危险控件，属高价值修复。无 Alembic / openapi。

### 任务 2.2　WP10　[纯前端]
- **变动来源**：登录页 · P1/P2 · 移动端布局 + 死链/注册占位（老板复核：注册入口改「请联系管理员开号」，勿接已禁用 register）。
- **改动点**：
  - `webapp/src/pages/Login.tsx:199`：双栏 `w-[460px] shrink-0` 加 `md:` 断点，窄屏隐藏左品牌栏、右栏 `w-full`（整体 `flex-col md:flex-row`）（1a）。
  - 死链「忘记密码?」(`:238`) /「使用恢复码」(`:308`)：给「请联系管理员重置」占位（1b）。
  - 注册入口/register 分支（`:90`）：改为「请联系管理员开号」提示，**移除对 `/api/auth/register` 的调用意图**（1c，该端点已按 C5 禁用）。
- **改成什么**：手机（375 宽）可正常登录；无死链/假成功；注册引导指向管理员开号。
- **验收标准**：preview 375 宽下登录表单完整可用、不溢出；点「忘记密码/恢复码」显占位提示；注册入口显「请联系管理员开号」，不发起 register 请求。
- **测试**：`build` + `tsc`；preview 375/768/桌面三断点；确认网络面板无 `/api/auth/register` 调用。
- **风险与注意**：登录是唯一共享入口，移动端破裂=用户进不来，务必真机断点验证。无 Alembic / openapi。

### 任务 2.3　WP11　[纯前端]
- **变动来源**：审计/事件流/K线 · P1/P2 · 时间时区统一本地化（追责「几点触发熔断」差 8 小时）。
- **改动点**：`webapp/src/api/stream.ts:239`（`envelopeToEventItem` 用 `occurred_at.slice(11,19)` 直切 UTC）改走本地时区格式化函数（与 Admin 的 `timePart()` 同源）（9b/M11b）；K 线 `KlineChart.tsx` 的 `timeScale` 配本地化（M8c）。
- **改成什么**：全站时间（审计/事件流/K 线轴）统一本地时区，与后台管理日志一致。
- **验收标准**：preview 同一事件在审计页与后台管理日志显示相同本地时间（不再差 8 小时）；K 线时间轴为本地时区。
- **测试**：`build` + `tsc`；本地时区格式化函数补 vitest（UTC ISO → 本地 HH:mm:ss）；preview 目视对齐。
- **风险与注意**：需确认 `timePart()` 现有实现可复用/提取为共享工具，避免两份格式化逻辑再度漂移。无 Alembic / openapi。

### 任务 2.4　WP12　[纯前端]
- **变动来源**：回测与绩效 · P1/P2 · Performance 绩效修正（恒绿=误导，绩效页是「要不要继续托付」核心依据）。
- **改动点**：
  - `webapp/src/pages/Performance.tsx:110`：净收益磁贴 `tone` 写死 `"pos"` 改为按 `netReturnPct >= 0` 动态取（6a）。
  - 「跑赢 HODL」：并列 sub 文案改醒目结论「+X% 跑赢 BTC HODL」，正向 mint 高亮差值（6b）。
  - 90 天对比曲线 `CompareCurve`：补 y 轴刻度 + hover 十字光标 tooltip，统一改用 `SparkLive` 同款（已引入 lightweight-charts）（6c）。
  - 盈亏比磁贴 `:125`：sub 标「avg R:R」实取 `profitFactor` 的定义不符 → sub 改「profit factor」或真上 avg R:R；磁贴「1.9:1」与统计卡「1.92:1」精度统一（6d）。
- **改成什么**：绩效数字颜色/定义/精度全部诚实自洽；核心卖点「跑赢 HODL」被强调；对比曲线可读任一时点。
- **验收标准**：preview 构造负收益时净收益磁贴显 rose（非恒绿）；跑赢 HODL 有差值高亮；对比曲线有轴/tooltip；盈亏比定义与精度全站一致。
- **测试**：`build` + `tsc`；preview 目视；如动态 tone 抽函数补 vitest（正→pos、负→neg、零处理）。
- **风险与注意**：涨跌色只用于真实正负是设计系统硬纪律，务必确认零收益的中性处理。数据口径若来自后端 `/api/performance/summary`，仅前端展示层调整，不改后端。无 Alembic / openapi。

### 任务 2.5　WP17　[纯前端]（打包收尾）
- **变动来源**：多模块 · P2 · 零散体验小改。
- **改动点**：
  - `webapp/src/components/**/TwoFaDialog.tsx:72-77`：用已返回的 `otpauth_uri` 渲染二维码（保留手输备选）（11b）。
  - 交易所卡片「已配置/未配置」大徽章补网络限定词（「测试网已配置」）（11e）。
  - 通知渠道未绑定时禁用开关 + 提示（`Settings.tsx:642-656`）（11d）——**绑定真值依赖后端 N2（任务 3.9）**；N2 未交付前，前端按「渠道无可用配置即禁用开关」的可得信息降级处理。
  - 编辑 SL/TP 弹窗加距现价 % + R:R（`Positions.tsx:217-219`，复用 OrderTicket rr 逻辑）（5c）。
  - `CoinAvatar`（`PositionsTable.tsx:6-9`）补主流币样式/回退 symbol 前 3 字母（M10a）。
  - `Risk.tsx:89` `label.includes("亏损")` 改数据字段驱动语义色（7c）。
  - `Modal` danger 确认按钮改实心 rose（仍在 DS 色板内）（M9c）。
  - 命令面板/顶栏搜索占位文案对齐实际能力（M3a/M2a）。
- **改成什么**：一批低成本一致性/安全微调，收敛零散病灶。
- **验收标准**：preview 2FA 显二维码；交易所徽章带网络词；未绑定渠道开关禁用带提示；编辑 SL/TP 显距现价%+R:R；非主流币显前 3 字母；Risk 语义色不再靠字符串匹配；danger 按钮实心 rose；搜索占位与能力一致。
- **测试**：`build` + `tsc`；preview 逐项目视。
- **风险与注意**：11d 的「已绑定」真值需 N2；未交付前用降级逻辑并留说明性注释指向 N2（不留裸 TODO）。二维码渲染注意不引入超范围新依赖（优先已有库/轻量 QR）。无 Alembic / openapi。

### 任务 2.6　WP18　[纯前端]（老板新增 · 整站响应式 shell）
- **变动来源**：F 类整站响应式（老板复核提级）· 移动端需实际看盘 + 操作。
- **改动点**：
  - `Sidebar.tsx`：<1024 折叠为图标栏/抽屉（M1c）。
  - 设置/后台内层 tab 栏（设置 200px/后台 180px）窄屏溢出 → 横滚/下拉（11f）。
  - `Topbar.tsx`：<1180 搜索框收图标、次要项折叠，**风控胶囊常驻不被裁**（2d/M2）。
  - `ChatDrawer.tsx`：窄屏全宽（M4c）。
  - `PositionsTable.tsx`：窄屏卡片化降级（M10c）。
  - （登录页移动端已在 WP10，不重复。）
- **改成什么**：375/768 窄屏下整站不横向溢出，可看盘、可执行关键操作（急停/平仓/确认）。
- **验收标准**：preview 375/768/1180 三断点：无横向滚动条溢出；侧栏可折叠/抽屉；风控胶囊始终可见；持仓在窄屏以卡片呈现；ChatDrawer 窄屏全宽。
- **测试**：`build` + `tsc`；preview 多断点目视 + 窄屏走一遍平仓/急停操作路径。
- **风险与注意**：shell 改动影响所有页面布局，须回归各页在桌面宽度下无退化。风控胶囊 spec 要求常驻，窄屏优先保它。无 Alembic / openapi。

---

## 阶段三: 依赖后端 · 端点先行

**目标**：交付需后端配合的资金安全与透明链能力，后端端点为对应前端任务前置。**WP1 原子急停为本阶段首个交付**（资金安全最高）。含后端还原盘点新缺口 N1/N2/N3。
**成功标准**：后端 `uv run pytest tests/unit/`（pre-commit 钩子）+ 必要 `tests/integration` 通过、ruff 0 警告；端点契约变更后**重新导出 openapi.json**；schema 变更走 `alembic revision -m` 生成骨架且**无外键**；前端联调后 `build` + `tsc` 通过、preview 显真实分步结果/拒绝/撤单/历史查询。审计经既有 ManualOps/审计链路落库。
**测试**：后端每个端点补 `tests/unit` 用例（含部分失败/权限/审计写入断言）；前端联调切 `webapp-real`(5174) 或 mock 契约对齐后 `build`+`tsc`。
**状态**：未开始

### 任务 3.1　WP1（后端）　[后端]　⚠高危（资金安全 · 原子急停 · 首交付）
- **变动来源**：设置页急停 · P1 · 后端新增原子急停端点（老板复核升级，非 try/catch 过渡）。
- **改动点**：新增端点，落在 `backend/src/controllers/api/v1/risk/commands.py`（现有 `close-all`(`:80`) / `pause`(`:128`) 同文件）。建议 `POST /api/commands/emergency-stop`（admin）。服务层复用现有 close-all（`order_execution`/ManualOps）与 pause（KillSwitch）逻辑，编排为一次调用。
- **改成什么**（契约）：
  - 请求：无 body（或 `{confirm: "STOP"}` 口令位，与前端 requireText 对齐）。
  - 行为：**fail-safe 语义**——先/同步保证引擎 `pause`（KillSwitch 置停，纯 DB 状态，可事务保证），再逐仓 close-all；因平仓涉及交易所外部副作用不可回滚，**逐仓结果以明细回执返回**，不静默。DB 侧状态（task_request / risk state）保持一致（单事务提交或明确补偿）。
  - 响应：`{ status: "ok" | "partial", engine_paused: bool, closed_count: int, failed: [{position_id, symbol, reason}], task_id?: str }`。部分失败返回 `partial` 且列出失败仓位与原因。
  - 审计：整个操作走既有 ManualOps/审计链路，`before_json/after_json` 记录引擎态与平仓结果。
- **验收标准**：单元测试覆盖：①全成功 → `ok`、engine_paused=true、closed_count=N；②部分平仓失败 → `partial` 且 `failed` 列出仓位+原因，但 `engine_paused` 仍为 true（fail-safe）；③无持仓 → `ok`、closed_count=0、引擎已停。审计记录写入可查。
- **测试**：`tests/unit/` 新增 emergency-stop 用例（成功/部分失败/空仓/权限 admin）；涉及交易所调用的部分失败用 mock adapter 注入异常；必要时 `tests/integration` 验证与 task_request 状态机协同。
- **风险与注意**：⚠ 最高危资金安全动作。核心不变量：**无论平仓是否部分失败，引擎必须已暂停**（避免仓位平了引擎仍在跑立刻重新开仓）。交易所平仓的外部副作用不可 DB 回滚，须以明细回执暴露而非假装原子成功。契约冻结后**重导 openapi.json**。无 schema 变更则无需 Alembic；若新增 task 类型枚举需迁移则走 `alembic revision -m`。

### 任务 3.2　WP1（前端）　[前端]　⚠高危
- **变动来源**：`Settings.tsx:694-703` `emergencyStop` 现为 closeAll+pause 两个非原子调用、无 catch。
- **改动点**：`webapp/src/pages/Settings.tsx:694-703` 改为单调用 `commandsApi.emergencyStop()`（新增于 `services.ts`），在急停弹窗内显示分步结果「已平 N 仓 / 引擎已停」，`partial` 时红字标出失败仓位与建议动作。保留现有 `STOP` 口令 + 滑点警示。
- **改成什么**：前端单调用原子端点，明确渲染 ok/partial 回执，绝不静默。
- **验收标准**：preview（契约对齐后）急停显「已平 N 仓/引擎已暂停」；mock partial 场景显红字失败明细。
- **测试**：`build` + `tsc`；`services.ts` 新方法 + mock handler 补齐；services.test.ts 覆盖 ok/partial 解析。
- **风险与注意**：**前置依赖任务 3.1**（后端端点 + openapi）。契约字段（status/failed/closed_count/engine_paused）为两端冻结点。无 Alembic。

### 任务 3.3　WP5（后端）+ WP5（前端）　[两端]
- **变动来源**：决策/审计透明链补全 · P1 ·（决策详情端点已存在；审计 before/after 后端已透出但前端 wire 层丢弃；Agent pending 前后值需后端）。
- **改动点**：
  - **前端（无后端阻塞，可先做）**：
    - 决策详情 `Decisions.tsx:115`：改调 `decisionsApi.detail(id)` → `/api/decisions/{id}`（`decisions.py:61`，已含 features + guard_events），渲染 features 快照 + 守卫全项（绿/红点区分，套守卫中文字典）（4a/4b）。
    - 审计 wire 层 `wire.ts:444-453` `fromWireAuditLog`：**保留** `before_json/after_json/resource_id`（后端 `admin.py:290` 已透出，当前前端映射丢弃），页面展示「旧值→新值」（10c）。
  - **后端**：
    - 验证/补齐审计**写入路径**：确认 runtime_config / settings / ManualOps 等配置变更在写 AuditLog 时确实填充 `before_json/after_json`（若现状写 null，补填），使前端有真实前后值可显（对应 C 类）。
    - Agent pending action 携带「键+旧值→新值」（M4）：`AgentHistoryItemRead`（`schemas/system_read.py:51`）与 SSE chat 的 pending 事件补 `key` / `old_value` / `new_value`，供**确认前**展示；`PilotAgentService` 在生成 pending action 时带上当前值与目标值。
- **改成什么**：决策可解释（features + 守卫全项）、审计记「谁把什么从 X 改成 Y」、Agent 确认前即显具体变更。
- **验收标准**：决策详情弹窗显 features + 8 项守卫（全过也显全绿）；审计条目显「LLM 温度 0.3→0.25」类前后值；ChatDrawer pending action 确认前即显 key+旧值→新值。后端单测断言配置变更审计写入含 before/after、agent pending 响应含 key/old/new。
- **测试**：后端 `tests/unit/` 补审计写入 before/after 断言 + agent pending 字段断言；前端 `build`+`tsc`，wire 映射补 vitest（保留 before/after/resource_id）。
- **风险与注意**：⚠ 触及审计链完整性。后端若改 pending action schema/agent 响应字段，**重导 openapi.json**。无 schema 表结构变更（AuditLog 已有 before_json/after_json 列）则无需 Alembic；agent pending 若需新表列则走 `alembic revision -m`（无外键）。

### 任务 3.4　WP13（后端）+ WP13（前端）　[两端]
- **变动来源**：Admin/账号安全 · P1/P2 ·（拒绝 pending 用户需后端端点；停用确认/初始密码脱敏为前端）。
- **改动点**：
  - **后端**：`backend/src/controllers/api/v1/system/admin.py` 现有 `POST /users/{id}/approve`(`:315`)，**新增拒绝/删除 pending 端点**（如 `POST /users/{user_id}/reject`，admin），PENDING → REJECTED（或删除），走审计。复用现有 approve 的权限/审计模式。
  - **前端**：待批准「拒绝」按钮 `Admin.tsx:151`（现无 onClick）接新端点 + `ConfirmDialog`（10b）；停用用户 `Admin.tsx:68-73` 加 `ConfirmDialog`+审计（10d）；邀请弹窗初始密码 `Admin.tsx:240-242` 明文 `Input` 换 `MaskedInput`（10e）；「最近活跃」`wire.ts:580` 先隐藏，接 N3 字段后再显（10f）。
- **改成什么**：账号准入具备「批准/拒绝」双闸且都有二次确认；停用有确认；初始密码脱敏；最近活跃列先隐藏不显假「—」。
- **验收标准**：preview 待批准用户可「拒绝」并弹确认，拒绝后状态变更且落审计；停用弹确认；初始密码为脱敏输入；用户表无空「—」最近活跃列。后端单测覆盖 reject（权限 admin、状态流转 PENDING→REJECTED、审计写入）。
- **测试**：后端 `tests/unit/` reject 用例；前端 `build`+`tsc`+preview。
- **风险与注意**：⚠ 账号准入是安全闸。reject 端点须 admin 鉴权 + 审计。前置：前端拒绝按钮依赖后端 reject 端点（**先做后端**）。契约变更**重导 openapi.json**。无表结构变更则无 Alembic（若加 REJECTED 状态枚举值且入库校验需迁移则走 `alembic revision -m`）。

### 任务 3.5　WP14（后端）+ WP14（前端）　[两端]　⚠高危（资金安全最后一道闸）
- **变动来源**：持仓与订单 · P1 · WORKING 挂单撤单（失效止损/止盈挂单是资金安全最后一道闸）。
- **改动点**：
  - **后端**：`backend/src/controllers/api/v1/execution/orders.py`（现有 precheck/place/list，**无撤单**）新增撤单端点（如 `POST /api/orders/{order_id}/cancel` 或 `DELETE /api/orders/{order_id}`，admin/trader）。服务层调交易所撤单 + 更新 Order 状态 + 幂等处理 + 审计（走 ManualOps 链路）。
  - **前端**：`Positions.tsx:152-188` 订单簿 WORKING 行末加「撤单」按钮 + `ConfirmDialog`（5a），接新端点。
- **改成什么**：可单独撤销 WORKING 状态的止损/止盈挂单，带二次确认与结果反馈。
- **验收标准**：preview WORKING 行显「撤单」，确认后该挂单状态变更/消失；后端单测覆盖撤单（幂等、状态流转、权限、审计、不存在/已成交订单的错误处理）。
- **测试**：后端 `tests/unit/` 撤单用例（正常/重复撤单幂等/已成交拒绝）；必要 `tests/integration` mock adapter 验证交易所撤单调用；前端 `build`+`tsc`+preview。
- **风险与注意**：⚠ 撤单涉及交易所真实操作与幂等。须处理「订单已成交/已撤销」的竞态，返回明确态而非静默。前置：前端依赖后端撤单端点（**先做后端**）。契约变更**重导 openapi.json**。无 schema 变更则无 Alembic。

### 任务 3.6　WP15（后端）+ WP15（前端）　[两端]
- **变动来源**：审计日志 · P1/P2 · 审计历史查询 + 搜索（审计价值在事后追溯，只看今日=残缺）。
- **改动点**：
  - **后端**：`admin.py:267` `GET /audit-logs` 现仅 `limit`。扩展查询参数：`from`/`to`（日期区间）、`actor`（操作人）、`q`（关键字）、分页（`page`/`page_size` 或游标）。事件流历史（M11 `/api/events/catchup` 仅当日）——按时段查询能力（可在 catchup 或审计端点提供）。
  - **前端**：`Audit.tsx:36`（写死「事件流·今日」）加日期区间控件 + 分页/无限滚动（9a）；过滤补 actor + 关键字搜索（`Audit.tsx:14-20` 现仅按 kind）（9c）。
- **改成什么**：审计/事件流可按日期区间 + 操作人 + 关键字检索并分页，支持事后追溯。
- **验收标准**：preview 可选日期区间查历史（非仅今日）、按 actor/关键字过滤、翻页；后端单测覆盖区间过滤/actor 过滤/分页边界。
- **测试**：后端 `tests/unit/` 查询参数用例（区间/actor/q/分页）；前端 `build`+`tsc`+preview。
- **风险与注意**：分页与区间查询注意索引/性能（审计表可能大）。前置：前端历史查询依赖后端参数扩展（**先做后端**）。契约变更**重导 openapi.json**。无 schema 变更则无 Alembic（若需加索引走 `alembic revision -m` 生成骨架填 upgrade/downgrade，无外键）。

### 任务 3.7　WP16（前端 + mock/后端校验）　[前端 + mock/后端]
- **变动来源**：策略实验室 · P1/P2 · 受控进化正确性（门槛不可逾越是受控进化可信度全部）。
- **改动点**：
  - **前端/mock**：promotable 严格反映「≥14 天且达标」，未满时禁用「申请灰度」+ 下方灰字显原因（8a，改 `mock/data.ts:117-123` 的 `promotable:true` 与按钮渲染逻辑，`Lab.tsx:196-198`/`:117-123`）；自动回滚署名改 `system` 而非 `admin`（8c，`mock/data.ts:449`）+ system 徽章；被禁用「申请灰度」按钮不再把拦截原因当按钮文字（改普通禁用 + 下方说明）。
  - **后端校验（已具备，仅需核对）**：`lab.py:86` promote 已服务端门槛校验、`lab.py:118` history 返回 rollback 触发原因。核对 `LabService.list_candidates` 返回的 `promotable` 是否严格按「≥14 天且达标」计算、自动回滚 history 的 `operator` 是否为 `system`；若 mock 与真后端口径不一致，以后端为准对齐 mock。
- **改成什么**：门槛不可逾越——未满 14 天/未达标不可申请灰度且显原因；系统自动动作署名 `system`。
- **验收标准**：preview 候选未满 14 天时「申请灰度」禁用并显原因；自动回滚条目署名 `system` 带徽章。后端（真模式）核对 promotable 计算与 history operator 一致。
- **测试**：前端 `build`+`tsc`+preview；若调后端 `LabService` 逻辑则补 `tests/unit/`（promotable 门槛计算、auto-rollback operator=system）。
- **风险与注意**：主要为前端/mock 与既有后端口径对齐；若发现后端 promotable/operator 口径确有 bug 才改后端（走单测）。无 openapi 契约变更（除非改 schema 字段）。无 Alembic。

### 任务 3.8　WP2（后端）· 后端还原 N1 · 调度器真实心跳　[后端]
- **变动来源**：侧栏引擎状态 M1b（「引擎运行中·48ms」写死）+ 附录 B 第 7 条 + 盘点新缺口 N1。
- **改动点**：`/api/health`（`health.py:22`）现不反映调度进程存活。后端补：调度器（`backend/src/schedulers/`，如 `strategy_pipeline_scanner`/`position_monitor_scanner`）每周期写 Redis 心跳 key（含时间戳）；新增或扩展端点暴露「引擎存活 + 最近心跳时间 + 延迟」（建议 `GET /api/system/engine-status` 落在 `controllers/api/v1/system/`，或扩展 health 返回 `scheduler` 段）。
- **改成什么**（契约）：`{ engine_alive: bool, last_heartbeat_at: iso, latency_ms?: int }`，供侧栏与主控台判断调度器是否真在盯盘。
- **验收标准**：调度进程运行时端点返回 `engine_alive:true` + 新鲜心跳；模拟调度停摆（心跳过期）→ 返回 `engine_alive:false`。前端（任务 1.6）接入后侧栏在调度挂掉时变琥珀/红显「连接中断」而非假「运行中」。
- **测试**：后端 `tests/unit/` 覆盖心跳新鲜/过期两态判定；心跳写入用 fake redis / 注入时钟。
- **风险与注意**：⚠ 「引擎是否真在盯盘」是关键安全信号，判定阈值（心跳过期多久算 dead）需明确。契约新增**重导 openapi.json**。无 schema 变更（Redis 心跳，非 DB）则无 Alembic。**前端 1.6 的侧栏真实存活位前置依赖本任务**。

### 任务 3.9　WP17（后端）· 后端还原 N2 · 通知渠道已绑定标志　[后端]
- **变动来源**：WP17 11d「通知渠道未绑定时禁用开关」+ 盘点新缺口 N2。
- **改动点**：`NotificationSettingsOut`（`schemas/settings.py:70`）现只有 `channels`(on/off) 与 `subscriptions`。补 `channels_configured: dict[str, bool]`（每渠道是否已配置可用凭据，如 Telegram token / Email SMTP），由 `settings` 服务据实际配置计算下发。
- **改成什么**（契约）：通知设置响应含 `channels_configured`，前端据此在渠道未绑定时禁用开关 + 提示（避免「开了但静默收不到关键熔断告警」）。
- **验收标准**：未配置凭据的渠道返回 `channels_configured[x]=false`；前端（任务 2.5 WP17）据此禁用开关。后端单测覆盖已配置/未配置两态。
- **测试**：后端 `tests/unit/` 覆盖 channels_configured 计算；前端联调 `build`+`tsc`。
- **风险与注意**：低风险纯读取标志。契约新增字段**重导 openapi.json**。无 Alembic。若本任务未排期，WP17 前端按可得信息降级（任务 2.5 已说明）。

### 任务 3.10（建议 V0.2）· 后端还原 N3 · 用户「最近活跃」字段　[后端]
- **变动来源**：Admin 用户表「最近活跃」全「—」（`wire.ts:580` 未映射）+ WP13 10f + 盘点新缺口 N3。
- **改动点**：`User` 模型加 `last_login_at`（或 `last_active_at`）字段；登录成功时更新；`/api/admin/users` 透出；前端 WP13 10f 接字段后再显。
- **改成什么**：用户表「最近活跃」显真实最近登录时间。
- **验收标准**：登录后该用户 `last_login_at` 更新，用户表显真实时间。
- **测试**：后端 `tests/unit/` 覆盖登录更新 last_login_at + 端点透出。
- **风险与注意**：**建议暂缓 / V0.2**——WP13 已决定「先隐藏」，非阻塞；且涉及 schema 变更。若排期：**必须走 `alembic revision -m "add user last_login_at"` 生成迁移骨架，人工填 upgrade/downgrade，无外键**；契约变更**重导 openapi.json**。V0.1 不做不影响其他任务。

---

## 交接说明

### 给 frontend-dev 的任务清单
- **阶段一（纯前端，可立即并行领取，彼此文件基本独立）**：1.1(WP3) / 1.2(WP4) / 1.3(WP6) / 1.4(WP7) / 1.5(WP9) / 1.6(WP2 前端连接态)。
  - 建议先做 **2.1(WP8 Modal focus trap)**，其 `Modal`/`ConfirmDialog` 增强被 1.2/1.4 的确认弹窗复用。
  - 1.4(WP7) 的守卫中文字典 `guardDict.ts` 为 WP5/WP13 共享，优先落地。
- **阶段二（纯前端）**：2.1(WP8，最先) / 2.2(WP10) / 2.3(WP11) / 2.4(WP12) / 2.5(WP17) / 2.6(WP18)。可与阶段一并行（不同文件）。
- **阶段三前端联调（有后端前置）**：3.2(WP1 前端，前置 3.1) / 3.3(WP5 前端部分可先做，pending 前后值待 3.3 后端) / 3.4(WP13 前端，前置 3.4 后端) / 3.5(WP14 前端，前置 3.5 后端) / 3.6(WP15 前端，前置 3.6 后端) / 3.7(WP16 前端/mock) / 2.5(WP17 11d 待 3.9)。
- 自验一律：`npm run build` + `tsc --noEmit` + preview(5173 mock) 走验收；复用现成 `ConfirmDialog`/`Modal`/`MaskedInput`/`Switch`/`SparkLive`，禁止新建同类组件。

### 给 backend-dev 的任务清单
- **首交付**：3.1(WP1 原子急停端点) ⚠高危——阶段三第一个，资金安全最高，fail-safe「引擎必停」不变量 + 分步回执 + 审计。
- **其余后端（可在 3.1 后并行）**：3.3(WP5 审计 before/after 写入填充 + Agent pending 前后值) / 3.4(WP13 拒绝 pending 端点) / 3.5(WP14 撤单端点) ⚠高危 / 3.6(WP15 审计历史查询参数) / 3.7(WP16 promotable/operator 口径核对) / 3.8(N1 调度心跳) / 3.9(N2 通知已绑定标志) / 3.10(N3 last_login_at，建议 V0.2)。
- 规范硬约束：`src.` 导入；控制器落 `src/controllers/api/v1/{execution,risk,strategy,system}/`；审计走既有 ManualOps/审计链路；**任何 schema 变更走 `alembic revision -m "..."` 生成骨架、人工填 upgrade/downgrade、无外键**；`tests/unit/`（pre-commit 强制）+ 必要 `tests/integration`；**端点契约变更后重导 openapi.json**。

### 契约冻结点（两端约定，改前必须同步）
- **WP1 原子急停响应**：`{ status: "ok"|"partial", engine_paused, closed_count, failed:[{position_id,symbol,reason}], task_id? }`（任务 3.1↔3.2）。
- **WP5**：`/api/decisions/{id}` 详情形状（features + guard_events，已存在）；审计 `before_json/after_json/resource_id`（已透出，前端停止丢弃）；Agent pending action 的 `key/old_value/new_value`（任务 3.3 新增）。
- **WP13**：拒绝端点路径与状态流转（PENDING→REJECTED）（任务 3.4）。
- **WP14**：撤单端点路径与幂等/错误态（任务 3.5）。
- **WP15**：审计查询参数 `from/to/actor/q/分页`（任务 3.6）。
- **N1**：引擎状态 `{engine_alive,last_heartbeat_at,latency_ms}`（任务 3.8↔1.6）。
- **N2**：通知 `channels_configured`（任务 3.9↔2.5）。
- **既有契约提醒**：前端 `strategyApi.toggle` 调 `PATCH /api/strategies/{id}`，后端为 `PATCH /api/strategies/{mode}`（`strategies.py:36`）——联调期核对 id/mode 口径是否一致，不一致则对齐（非本批新增功能，属契约核对项）。

### 暂缓 / 否决（不进本计划，见交接清单）
侧栏徽章 5/2(M1a，已删) / mock dup key 739(4e) / 图表深度 aria(M8a) / 动画绑真实守卫(M6b，依赖 decision.progress) / Agent 模型分工可配(11c) / 命令面板快捷动作(M3b) / 两套日志交叉链接(9d) / 日报选历史某天(9e，依赖 WP15) / reduce-only 精简校验(5d) / 磁贴统计卡重复维度(6e)。N3(用户最近活跃) 建议 V0.2。

---

> 全部阶段完成后按 CLAUDE.md 约定删除本文件；进行中随时更新各任务「状态」。
