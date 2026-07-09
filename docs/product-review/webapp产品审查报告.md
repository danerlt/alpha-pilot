# AlphaPilot webapp 前端 · 全量产品审查报告

> 审查时间：2026-07-08
> 审查方式：`product-advisor` agent，webapp dev（mock 模式）实跑登录，每个页面/模块 preview 亲眼所见（无障碍树 / DOM / `preview_inspect` 实测取值 + 源码 `文件:行号` 互证），非纯代码想象。
> 覆盖范围：11 个页面 + 11 类全局模块，无遗漏。
> 定位：仅产品/UX 审查与建议，**不含代码改动**。后续走「需求变动评审 → 计划制定 → 前后端开发」四 agent 流水线落地。

## 环境复用信息

- **webapp 实际路径**：`E:\ai\alpha-pilot\webapp`（不是 Design System 里的 ui_kits）。页面 `webapp/src/pages/`，组件 `webapp/src/components/`，API/mock `webapp/src/api/`。
- **启动/mock**：`npm run dev`（5173）默认即 mock（`apiBaseUrl` 为空 → MSW 拦截）。`.claude/launch.json` 已有 `webapp`(5173)/`webapp-real`(5174)。
- **登录**：登录页「以演示账户进入」，或任意非空邮箱+密码。
- **设计系统纪律**（所有建议须尊重）：色值只用 `--ap-*` token 禁硬编码；数字用 JetBrains Mono + tabular-nums；violet 仅用于 AI 产物；涨跌色只用于真实数值正负、不做装饰；禁 emoji，图标用 lucide-react；侧栏 240px、卡片圆角 12px 等见 `AlphaPilot Design System/handoff/01_设计系统集成指南.md`。

---

# 一、执行摘要（Executive Summary）

这套 webapp 的**视觉与设计系统执行是顶尖的**：`--ap-*` token 零硬编码色、数字统一 JetBrains Mono + tabular-nums、violet 严格限定 AI 产物、涨跌色克制、组件复用度高、动效有节制。**信任叙事**（受控进化、只读工具+人工确认、硬风控不可 AI 改）和**危险操作口令确认**（MAINNET / STOP / CLOSE ALL）说明产品真正理解了「把真钱托付给 AI」这件事。设置页是全站安全设计标杆。

问题高度收敛为 **9 类共性病灶**，几乎每一类都直接触及交易系统的信任、风控或资金安全底线。

## 九类共性问题

| 分类 | 病灶 | 典型位置 |
|---|---|---|
| **A. 假控件 / 假数据** | 看起来能点/能信、实则无功能或写死假值 | 顶栏 AUTO 不可点、通知铃铛死按钮带误导红点、侧栏徽章 5/2 与「引擎运行中·48ms」写死、Risk 交易对开关与「添加交易对」不可交互、Admin 权限矩阵可点样式却无功能、「拒绝」死按钮、事件流「LIVE」恒亮 |
| **B. 静默吞异常 / 无状态反馈** | 关键操作/数据缺「成功·失败·是否新鲜」回执 | 紧急停止 close-all+pause 非原子且失败无提示、无 WS 连接态/数据新鲜度指示 |
| **C. 透明链在 wire 层被削** | 「AI 为什么这么做、谁改了什么」反复在数据映射层丢信息 | 决策详情不调详情端点（features/守卫看不到）、守卫只显失败项、审计日志丢「旧值→新值」、Agent pending action 确认前不显具体变更 |
| **D. 现货产品混入合约概念** | 与「V0.1 仅现货做多」定位矛盾 | 行情页资金费率/OI/标记价/指数价/结算、下单「做空」、PositionsTable 做空分支、Lab「资金费率过滤」候选 |
| **E. 风控阈值文案硬编码且自相矛盾** | 熔断锚点对不上 | HaltBanner −2.00% vs 全站 3%、Dashboard 磁贴「阈值 −8%」写死 |
| **F. 响应式 shell 缺失** | 窄屏横向溢出、风控胶囊被裁 | 240px 侧栏 + 顶栏 + 设置/后台内层 tab 栏在 <1180 溢出、登录页移动端表单溢出屏外 |
| **G. 英文原始 key 直呈用户** | 机器串给人看 | 守卫预检 `qty_valid/stop_loss_set/...`、决策/审计 action code、features key |
| **H. 可访问性系统性缺口** | 键盘/读屏不可达 | Modal/ChatDrawer 无 focus trap、表单 label 未关联、图表无 aria 文本替代 |
| **I. 强制动画阻塞阅读** | 每次进页重放 ~4s 才见结论 | StreamingDecision 主控台 hero / 决策流首条 |

## 最该优先做的 5 件事（按投入产出排序）

1. **清理「假控件/假数据」（A 类）——低成本、高信任回报**。AUTO、通知铃铛、侧栏徽章/引擎状态、Risk 交易对开关、Admin 权限矩阵与「拒绝」、事件流 LIVE：能接真值的接真值，接不了的置灰/移除/改文案。直接消除「系统在骗我」的观感。（多为前端）
2. **修紧急停止的原子性与反馈（B 类）+ 全站连接态指示**。急停加 try/catch 与「已平 N 仓/引擎已停」回执、暴露部分失败；WS 连接/新鲜度驱动「LIVE→重连中→已断开」。直接关系资金安全。（需少量后端配合）
3. **补全决策/审计透明链（C 类）**。决策详情调 `/api/decisions/:id` 显示 features + 守卫全项；审计/管理日志 detail 带「旧值→新值」；Agent 确认前显具体变更。（需后端透传字段）
4. **统一熔断阈值取真值 + 清理现货页合约字段/做空（E + D 类）**。删 HaltBanner/磁贴魔数改读 `risk/limits`；行情与下单去掉资金费率/OI/做空等永续概念。一次性消除两类矛盾。（前端为主）
5. **补 Modal focus trap + 决策卡三变体统一保留 SL/TP + 关掉强制重放（H + I 类）**。一个 focus trap 全站弹窗受益；三变体都保留止损止盈；StreamingDecision 只对新实时决策播一次。（纯前端）

---

# 二、逐页详细审查

## 1. 登录 / 2FA（`Login.tsx`）

**P1 应改**
- **移动端布局破裂** — `Login.tsx:199` 双栏 `w-[460px] shrink-0` 无单栏降级；375 宽下右表单溢出屏外、左品牌栏塌成 ~0 宽。登录是唯一共享入口，手机点链接进来基本无法登录。**改**：加 `md:` 断点，窄屏隐藏左栏、右栏 `w-full`；或整体 `flex-col md:flex-row`。

**P2 可优化**
- **死链**：「忘记密码?」(`Login.tsx:238`)、「使用恢复码」(`:308`) 无 `onClick` 的 `<span>`，点了没反应。接流程或先给「请联系管理员重置」占位。
- **注册假成功**：register 分支只 `setRegistered(true)` 本地态(`:90`)，不调后端。联调前需接 `/api/auth/register`。
- 做得好：demo 账户降门槛；2FA 六格自动跳格 + 满格自动提交 + 错误清空重输(`:121-141`)。

## 2. 主控制台（`Dashboard.tsx` / `Topbar.tsx`）

**P1 应改**
- **无「接管 / 急停」入口** — 顶栏「AUTO」静态 `<div>`(`Topbar.tsx:82`)不可点；通知铃铛(`:73`)有红点却无 `onClick`、无 `aria-label`。「把钱交给 AI」的核心信任=「我随时能一键接管/急停」，现在急停埋在设置页危险区，监控现场反而没有，死红点还制造焦虑。**改**：「AUTO」做成引擎开关(接 `commands/pause`/`resume`) 或顶栏加常驻急停(接 `close-all`+`pause`，复用 `ConfirmDialog`)；铃铛接通知抽屉或去红点 + 补 `aria-label`。
- **熔断阈值文案硬编码且自相矛盾** — `HaltBanner.tsx:48-49` 写死「≥ 阈值 −2.00%」，但 `MAX_DAILY_LOSS_PCT`=3%，Dashboard 磁贴又写死「阈值 −8%」(`Dashboard.tsx:163`)。**改**：统一从 `risk/limits` 接口取值渲染。

**P2 可优化**
- **AI hero 每次进页强制重放 ~3.9s 动画**，期间看不到入场/SL/TP。动画只对新到达的实时决策播。
- **窄屏顶栏裁切**：768 宽下横向滚动，风控胶囊/AUTO 被挤出（风控胶囊 spec 要求常驻）。<1180 时搜索框收成图标、次要项折叠。

## 3. 行情（`Market.tsx` / `OrderTicket.tsx`）

**P1 应改**
- **现货产品显示永续合约字段** — 市场卡与 AI 解读展示「资金费率 / 持仓量 OI / 标记价格 / 指数价格 / 下次结算」(`Market.tsx:232-238,275-301`)，Binance 现货根本没有，同页却写「V0.1 仅支持现货做多」。**改**：换现货字段（24h 成交额/买一卖一/价差/成交笔数）或移除。
- **下单面板给了「卖出 / 做空」**(`OrderTicket.tsx:104`) — 现货做多无法做空，SELL=卖已持仓，标「做空」概念错误、诱导不支持的操作。**改**：移除做空，SELL 改「卖出(平仓)」绑 reduce-only，或 V0.1 只留买入侧。
- **手动下单无二次确认** — 点「买入 BTC」直接 `ordersApi.place`(`OrderTicket.tsx:86-95`) 真实下单。**改**：提交前弹 `ConfirmDialog` 摘要（方向/数量/名义/SL/TP/预检结论）。

**P1 应改（由 P2 提级，老板现场确认）**
- **守卫预检项显示原始英文 key** — `OrderTicket.tsx:227` 渲染 `c.check`、`:228` 渲染 `c.note`，用户看到 `sl_distance_out_of_range`/`chaotic_regime`/`rr=3.24` 这类机器串，读不出「为什么下不了单」。**改**：加守卫中文字典（见附录 A），左标签走字典、右侧拦截态显示一句话中文原因、机器串收进 `title` tooltip。

**P2 可优化**
- **仓位百分比按钮误导**：公式带 `*0.1`(`OrderTicket.tsx:155`)，点「100%」实际只下 ~10% 名义，与「满仓」心智不符。让按钮语义与计算自洽。
- 做得好：预检严格走后端不前端复算；HALTED 时仅允许 reduce-only 降级正确。

## 4. AI 决策流（`Decisions.tsx`）

**P1 应改**
- **详情弹窗看不到 features 快照与守卫逐项** — 详情复用列表对象(`Decisions.tsx:115`)，列表数据不含 features/guards；已有 `/api/decisions/:id` 详情端点（含 features + guard_events，`wire.ts:229`）**却从未被调用**。spec P4 要求详情展示完整 features + 守卫逐项，缺了=不可解释=不可信。**改**：点击时 `useQuery(['decision', id])` 拉详情端点渲染。

**P2 可优化**
- **守卫逐项只显失败项**（mock `.filter(g => !g.ok)`，`wireMocks.ts:140`），看不到「8 项全过」全貌。保留全部用绿/红点区分。
- **卡片样式切换器(Stepper/Timeline/Graph)** 放页头属调试向，是终端用户认知噪音，移到设置页或移除。
- 首条决策每次进页重放动画（同主控台）。
- **控制台刷屏 duplicate key「739」**（mock 派生 id 不唯一，`wireMocks.ts:107`），仅 mock，但联调期刷错误、可能导致卡片被 React 省略。

## 5. 持仓与订单（`Positions.tsx` / `PositionsTable.tsx`）

本页最扎实——平仓二次确认、编辑 SL/TP 走守卫预检、空态引导都到位，是标杆。

**P1 应改**
- **WORKING 挂单无法单独撤单** — 订单簿(`Positions.tsx:152-188`)只读，无撤单/改单；磁贴显示「活跃挂单 2·SL×1·TP×1」但点不动。挂着的止损/止盈单是资金安全最后一道闸，异动想撤失效挂单只能绕道持仓行「编辑」。**改**：WORKING 行末补「撤单」按钮复用 `ConfirmDialog`（需后端撤单端点）。

**P2 可优化**
- 编辑弹窗守卫预检显示英文 key(`Positions.tsx:225`)，套用附录 A 字典。
- **编辑 SL/TP 弹窗缺量化反馈** — 只显入场/标记(`:217-219`)，不显新止损距现价 % 和改后 R:R。**改**：加一行 mono 数字（距标记价 % + R:R，复用 OrderTicket rr 逻辑）。
- 仅调 SL/TP 的减仓操作却跑 `max_position_size` 开仓向校验(`:49-66`)，预检项与语义不匹配，让后端对 reduce-only 返回精简项。
- 做得好：平仓确认警示「此操作绕过 AI 决策，直接提交交易所执行」(`:254-264`)；`ConfirmDialog` 内置 `requireText` 口令。

## 6. 回测与绩效（`Performance.tsx`）

**P1 应改**
- **「净收益」磁贴颜色写死 `tone="pos"` 恒绿**(`Performance.tsx:110`)，无论实际正负。绩效页是用户判断「要不要继续托付」的核心依据，负收益仍显绿=误导，违背「涨跌色只用于真实正负」纪律。**改**：`tone` 按 `netReturnPct >= 0` 动态取。

**P2 可优化**
- **核心卖点「跑赢 HODL」未强调** — 18.42% vs 11.07% 仅并列 sub 文案(`:110`)，无 ▲/差值高亮。**改**：加醒目结论「+7.35% 跑赢 BTC HODL」，mint 正向色。
- **90 天对比曲线无坐标轴/刻度/悬停**（`CompareCurve :26-56` 只画线不画轴），读不出任一时点收益率。**改**：补 y 轴刻度 + hover 十字光标 tooltip（复用 SparkLive 同款，已引入 `lightweight-charts`）。
- 「盈亏比」磁贴 sub 标「avg R:R」实取 `profitFactor`(`:125`)，定义不符；磁贴「1.9:1」与统计卡「1.92:1」精度不一。**改**：sub 改「profit factor」或真上 avg R:R，精度统一。
- 净收益/胜率/盈亏比 在 6 磁贴与统计卡重复，统计卡换 Sortino/最长连亏/平均盈亏单等新维度。

## 7. 策略与风控（`Risk.tsx`）

**P1 应改**
- **硬风控表承诺可改、实则无任何修改入口** — 警示条写「修改需 admin 权限并记录审计」(`Risk.tsx:74-76`)，但限额表(`:78-96`)纯只读，全页无编辑按钮。admin 想调熔断阈值无路可走，文案还暗示「能改」→ 困惑、疑权限出错。**改**：(a) 每行补「修改」→ `ConfirmDialog`（带口令 + `POST /api/config/runtime` + 落审计）；或 (b) 若有意锁死，改文案为「硬风控阈值仅可由部署配置调整，运行期不可变更」。
- **交易对管理是死控件** — ON/OFF 静态 `<span>` 非开关(`:116`)，「添加交易对」按钮无 onClick(`:119`)、点击无反应。DOGEUSDT 显示 OFF 却无法启用。交易对开关是「让 AI 别碰某币」的手闸，假按钮应急时点不动。**改**：ON/OFF 换 `Switch`+`ConfirmDialog`（启停落审计）；「添加」接真实表单或置灰标「即将支持」。

**P2 可优化**
- 硬风控值靠 `label.includes("亏损")` 判红(`:89`)较脆，将来新增含「亏损」项会误红，改由数据字段驱动语义色。
- 做得好：警示条「AI 不可绕过或自我修改」(`:71-77`) 对「凭什么敢托付」回答到位；启停确认区分文案且说明「已有持仓止损止盈监控不受影响」。

## 8. 策略实验室（`Lab.tsx`）

受控进化叙事、影子进度、影子 vs 线上逐项对比(优者标 ▲)、灰度/终止确认都完整，是强页。

**P1 应改**
- **门槛文案与按钮状态自相矛盾** — 说明条写「影子期 ≥14 天 且指标优于基线方可申请灰度」(`Lab.tsx:196-198`)，但候选 #1 处于「第 10/14 天(72%)」却已亮起可点的「申请灰度上线」(mock `promotable:true`，`:117-123`)。受控进化可信度全建立在「门槛不可逾越」上，没满 14 天就能申请=门槛是摆设。**改**：promotable 严格反映「≥14 天且达标」；未满时禁用 + 显示原因。

**P2 可优化**
- 候选 #2「加入资金费率过滤(>0.05% 不追多)」(`mock/data.ts:429`)，资金费率是永续概念、现货无此项。**改**：换现货有意义候选（成交量/波动率/价差过滤）。
- 进化历史「自动回滚」条目署名 `admin`(`mock/data.ts:449`)，系统自动动作应记 `system`，误记人工会误导审计归因。**改**：operator 记 `system` 并标 system 徽章。
- 被禁用的「申请灰度」按钮把拦截原因当按钮文字（超长），改普通禁用按钮 + 下方灰字说明。
- 做得好：流水线图示、影子进度、▲ 标记、灰度/终止均走 `ConfirmDialog` 且讲清「小仓位真实运行/回撤超限自动回滚/服务端二次校验」。

## 9. 审计日志（`Audit.tsx`）

**P1 应改**
- **审计范围锁死「今日」，无历史/日期范围/分页** — 标题写死「事件流·今日」(`Audit.tsx:36`)，仅今日 catchup，spec P9 要求全量。审计价值在事后追溯，只能看今天=残缺，出问题无法回溯。**改**：加日期区间控件 + 分页/无限滚动（需后端按时段查询）。
- **事件时间显示 UTC 而非本地时区** — `envelopeToEventItem` 直切 ISO 的 UTC 段(`stream.ts:239`)显示「06:23:09」，而 Admin 管理日志用 `timePart()` 本地化显示「14:23:08」，两页差 8 小时、自相矛盾。追责「几点触发熔断」会对不上。**改**：审计时间也走 `timePart()` 统一本地化。

**P2 可优化**
- 过滤仅按 kind(`Audit.tsx:14-20`)，无按操作人/关键字搜索。加搜索 + actor 过滤。
- 「审计日志」（事件流）与后台「管理操作日志」两套数据源、命名相似易混。做交叉链接或加指引。
- AI 日报卡是亮点，标注「自动生成」并支持选历史某天。

## 10. 后台管理（`Admin.tsx`）

**P1 应改**
- **权限矩阵是假可点的只读表** — 非 Owner 格渲染 `cursor-pointer`+mint 悬停(`Admin.tsx:387-395`)，但 44 个格子全部 `onclick===null`。RBAC 是安全核心，管理员误以为「点一下就收回下单权限」实则毫无变化——以为已降权、实则权限仍在，可能酿成越权。**改**：(a) 接真实授权/撤销(点击→`ConfirmDialog`+后端+审计)；或 (b) 若有意只读，去掉 `cursor-pointer`/hover、标「固定角色模型不可自定义」。
- **待批准用户「拒绝」是死按钮**(`Admin.tsx:151` 无 onClick) — 只能批准或放着，账号准入少了「拒绝」这一半安全闸。**改**：接拒绝/删除 pending 端点 + 二次确认。
- **管理日志丢失「改了什么」的实质** — `fromWireAuditLog`(`wire.ts:444-453`)只用 action+resource 拼 detail，mock 原有「LLM 温度 0.3→0.25」被 wire 层丢弃。审计只记动作类型、不记前后值，追责说不清「谁把什么从 X 改成 Y」=形同虚设。**改**：wire 层保留 detail/before-after/resource_id 并展示。

**P2 可优化**
- 停用用户一键生效无确认(`Admin.tsx:68-73`)，误点即停用他人（尤其 admin）。**改**：停用走 `ConfirmDialog`+审计。
- 邀请弹窗「初始密码」用明文 `Input`(`Admin.tsx:240-242`)，而 API Secret 用了 `MaskedInput`，肩窥风险。**改**：换 `MaskedInput`+强度提示。
- 用户表「最近活跃」全为「—」(`wire.ts:580` 未映射)，无信息量，接后端或先隐藏。

## 11. 设置（`Settings.tsx` / `form.tsx` / `TwoFaDialog.tsx`）

**全站安全设计标杆。** 实测确认：API Key 脱敏尾 4 位 + 留空不改（两网络独立）、Secret 用 `MaskedInput`（密码态+显隐+阻止密码管理器回填）、testnet=cyan「模拟不涉真金」/mainnet=rose「真实资金·切勿开提现」、提现权限「必须关闭!」用红三角/绿锁、切换网络与保存 Key 分离、切主网需输 `MAINNET` 口令、紧急停止需输 `STOP`+滑点警示、关 2FA 需当前动态码。都击中资金安全要害。

**P1 应改**
- **紧急停止是「全平+停机」两个非原子调用，失败无反馈** — `emergencyStop`(`Settings.tsx:694-703`)先 `closeAll()` 再 `pause()`，无 `catch`。若 closeAll 成功但 pause 抛错，弹窗静默、不提示，用户不知「仓位平了没、引擎停了没」。最高优先级资金安全动作部分失败（仓位已平但引擎仍在跑、可能立刻重新开仓）却静默=误以为已安全停机→真金损失，违背「绝不静默吞异常」。**改**：①try/catch 弹窗内红字标哪一步失败+建议动作；②理想上后端提供原子「紧急停止」端点，前端单调用+明确成功/部分失败态；至少先显示「已平仓 N 笔/引擎已暂停」回执。

**P2 可优化**
- 开启 2FA 只给明文密钥、无二维码(`TwoFaDialog.tsx:72-77`)，`otpauth_uri` 已返回却没用。手输 32 位易错、降低开启意愿。**改**：用 `otpauth_uri` 渲染二维码，保留手输备选。
- Agent 模型分工只读不可配(`Settings.tsx:575-593`)，spec P11 含配置意图。**改**：每行加模型 Select，保存走 runtime config。
- 通知渠道可开关但无绑定入口 — Discord「未绑定」却能 toggle on(`Settings.tsx:642-656`)，开了没绑定=静默收不到告警，而熔断通知标「关键」。**改**：渠道行加「绑定/配置」入口，未绑定时禁用开关+提示。
- 交易所卡片「已配置/未配置」大徽章跟随配置视图切换，易误读成整体已配置。徽章补网络限定词（「测试网已配置」）。
- 响应式：内层 tab 栏（设置 200px/后台 180px）窄屏不折叠，叠加 240px 侧栏致整页横向溢出（根因 shell 非响应）。

---

# 三、逐模块详细审查（全局组件）

## M1. 侧栏 Sidebar（`Sidebar.tsx`）

**P1 应改**
- **导航徽章硬编码假数字** — `NAV` 里 `badge: 5`(AI 决策)、`badge: 2`(策略实验室) 写死(`Sidebar.tsx:23,27`)。徽章语义=「有 N 件事待你看」，恒定假值=狼来了/处理完不消失。**改**：接真实计数（未读决策/待批准候选），无数据不显示。
- **引擎状态「引擎运行中·48ms」是静态假象**(`:119-121`) — 绿点脉冲、文案、延迟全写死。这是「AI 是否真在替我盯盘」的关键信号，调度实际挂了仍显「运行中」=危险的虚假安心。**改**：接真实心跳/健康检查(`/api/health` 或 WS 心跳)，异常变琥珀/红显「连接中断」，延迟取真实 RTT。

**P2 可优化**
- 侧栏 240px 固定、无移动端折叠，窄屏是整站横向溢出主因。<1024 收成图标栏或抽屉。

## M2. 顶栏 Topbar（`Topbar.tsx`）

（AUTO 不可点 / 通知铃铛死按钮 / 风控胶囊窄屏被裁 已在页面 2 详列，此处补充）

**P2 可优化**
- 风控胶囊仓位/日损/regime 是实时真值(`useApp().risk`)，正确，保留；问题只在窄屏被挤掉，窄屏优先保胶囊、搜索框收图标。
- 顶栏搜索占位「搜索交易对、决策、策略…」与 CommandPalette 实际能力不符，两处文案对齐。

## M3. 命令面板 CommandPalette（`CommandPalette.tsx`，⌘K）

⌘K 可唤起，ArrowUp/Down/Enter/Esc 键盘可达，输入自动聚焦，空态、背景关闭都在。

**P1 应改**
- **搜索能力名不副实** — 占位承诺搜「决策/策略/场景」，实际只 filter 页面 label 与 symbol(`CommandPalette.tsx:54-72`)，搜「停」无结果、「场景」被 `USE_MOCK` 门控(`:66`)。命令面板是专家高效入口，承诺搜不到就弃用；两处占位还互相矛盾。**改**：①文案与能力对齐；②扩展搜索源到决策(按 id/symbol)、策略、持仓，命中跳详情。

**P2 可优化**
- 无快捷动作（急停/全平/暂停/切网络）。可加少量高频**安全**动作（危险动作一律经 `ConfirmDialog` 口令确认），V0.1 可暂缓。
- 容器是 `div` 非 `role="dialog"`，输入无 `aria-label`，补 ARIA。

## M4. Pilot AI 对话抽屉 ChatDrawer（`ChatDrawer.tsx` / `agentStream.ts`，⌘J）

⌘J 可唤起。副标「只读工具·写操作需人工确认」、空态引导 + 快捷 chips、工具调用轨迹、流式 delta、pending action→「应用修改(需确认)」→ConfirmDialog→落审计，错误态内联「⚠ 对话请求失败(500)」都到位。

**P1 应改**
- **抽屉无 focus trap、Esc 不关闭**(`ChatDrawer.tsx:151-157`) — 仅背景点击关闭，Tab 焦点逃逸到背后页面。**改**：复用 Modal 的 Esc 监听 + focus trap，打开聚焦输入、关闭归还焦点。

**P2 可优化**
- **pending action 确认前只显泛化文案**（`:55,102`「待确认的配置修改」），确认后才变「MAX_DAILY_LOSS_PCT → 2」。让人在信息不足下确认硬风控变更。**改**：pending action 携带并展示「键+旧值→新值」，确认弹窗也明示。
- 抽屉宽 400px 固定、窄屏未适配；低优先。

## M5. AI 决策卡三变体 DecisionCard（`DecisionCard.tsx`）

三变体均可渲染，视觉精致，violet 仅用于 AI 产物、守卫色语义正确。

**P1 应改**
- **Timeline 与 Graph 变体丢失止损/止盈/入场/仓位** — 价位磁贴网格只在 Stepper 里渲染且需 `d.sl !== undefined`(`DecisionCard.tsx:88`)；Timeline/Graph 全无。变体存 localStorage，一旦选了 Timeline/Graph，主控台 hero + 决策流列表处处看不到 SL/TP。止损止盈是「这笔冒多大风险」最关键信息，换卡片样式就藏掉=风险沟通缺失。**改**：三变体都保留 SL/TP/入场/仓位（作通用头部/摘要条），变体只改「决策过程」可视化形态。

**P2 可优化**
- 默认变体 Stepper(`variant.ts:8`) 正确，保留。Graph 需 `min-w-960px` 横向滚动(`:246`)，定位为「深看单条」详情视图更合适，不做列表默认。
- Stepper 底部 `trace · {d.id.replace("d_","")}`(`:159`) 与 mock id 派生碰撞相关（真后端整数 id 无碍）。

## M6. 流式决策 StreamingDecision（`StreamingDecision.tsx`）

逐段点亮管道（采集→推理→守卫→裁决→执行）+ 完成展开 + 「重放」，叙事感强。

**P1 应改**
- **每次进页/换 symbol 强制重放全动画，期间读不到结论** — `motion` 默认 true，`useEffect` 依赖 `d.id`(`:54-62`)，5 段累计约 3.9 秒(`:12-18`)才展开完整卡；主控台 hero 与决策流首条受影响。监控面板第一诉求是「即刻看到最新决策结论」。**改**：动画只对新到达的实时决策播一次（由 WS `decision.complete` 触发），刷新/返回直接展开，保留手动「重放」，可加「跳过动画」偏好。

**P2 可优化**
- 动画阶段文案（「8 项硬风控校验」）是静态脚本，未与真实守卫结果绑定；真实流应由后端 `decision.progress` 驱动（代码注释已标此意图，待接真）。

## M7. 熔断横幅 HaltBanner（`HaltBanner.tsx`）

WARN/HALTED 分色（amber/rose）、HALTED 斜纹底 + 阴影、行动按钮（查看风控日志/手动恢复/我知道了）、`role="alert"` 都在，视觉冲击到位。

**P1 应改**
- **熔断阈值文案硬编码 −2.00%，与全站 3% 矛盾** — `HaltBanner.tsx:48-49` 写死「日损…≥ 阈值 −2.00%」及「距阈值…（以 -2.0 计算）」，而 `MAX_DAILY_LOSS_PCT=3%`。熔断线是风控信任锚点，横幅说「-2% 熔断」而设置说「3%」直接动摇信任。**改**：阈值从 `risk/limits` 真值渲染，WARN 的「距阈值」也据真值算。

## M8. 图表类（`KlineChart.tsx` / `SparkLive.tsx` / `Sparkline.tsx` / `AnimatedNumber.tsx`）

质量高：K 线用 lightweight-charts（蜡烛+量能+SL/TP/入场价格线+现价虚线+十字光标 OHLC），颜色全运行时解析 `--ap-*` token（零硬编码），ResizeObserver 驱动；SparkLive（主控台权益曲线）**有**十字光标+tooltip+「自起点 %」（更正批 2：缺 tooltip 的是 Performance 的 `CompareCurve`，不是 Dashboard 权益曲线）；AnimatedNumber 用 tabular-nums+涨跌闪色+后台标签页直接落值。

**P2 可优化**
- **所有图表对读屏/键盘不可达** — KlineChart(canvas)、SparkLive/Sparkline(SVG)、AnimatedNumber(`<span>`) 均无 `role`/`aria-label`/文本替代。**改**：图表容器加 `role="img"`+`aria-label`（如「近 96 点权益曲线，当前 $128,450，较起点 +2.3%」）；关键 AnimatedNumber 补 `aria-live`。
- Performance 的 `CompareCurve`/`MonthlyBars` 是独立内联 SVG，无轴/刻度/tooltip，与成熟的 SparkLive 不一致。统一改用 SparkLive 同款或至少补轴标签。
- K 线时间轴 lightweight-charts 默认 UTC，与站内本地时区诉求不一致；配 `timeScale` 本地化，与事件流时区问题一并处理。

## M9. 弹窗原子 & 表单原子（`Modal.tsx` / `ConfirmDialog.tsx` / `TwoFaDialog.tsx` / `form.tsx`）

一致性好：Modal 统一 Esc+背景关闭+`role="dialog"` `aria-modal`+关闭按钮 `aria-label`；ConfirmDialog 支持 `requireText` 口令（MAINNET/STOP 前确认按钮禁用）、danger 变体；MaskedInput 密码态+显隐+阻止密码管理器；Switch 有 `role="switch"`/`aria-checked`。

**P1 应改**
- **Modal 无 focus trap、无归还焦点、无初始聚焦** — 只处理 Esc(`Modal.tsx`)，Tab 焦点未锁在对话框内、关闭不还焦点。ConfirmDialog/EditUser/编辑SLTP 全部继承此缺陷。这些弹窗含**平仓、切主网、紧急停止**等资金安全操作，Tab 焦点逃逸到背景可能误触危险控件。**改**：给 Modal 加 focus trap（打开聚焦首个可聚焦元素、循环 Tab、关闭归还焦点），全站弹窗一次受益。

**P2 可优化**
- `Input` 无关联 `<label for>`，`Field` label 是纯 `<div>`(`form.tsx:16-20`)，未与 input 编程关联；`Select` 同样。读屏念不出字段名、点 label 不聚焦。**改**：`Field` 用 `<label>` 包裹或 `htmlFor`/`id` 关联。
- ConfirmDialog danger 确认按钮用 `bg-rose-soft`（14% 透明），对「确认平仓/紧急停止」对比偏弱，破坏性确认可用实心 rose（仍在 DS 色板内）。
- TwoFaDialog 开启态只给明文密钥、无二维码，`otpauth_uri` 已有可渲染 QR。

## M10. 持仓表 PositionsTable（`PositionsTable.tsx`，作为复用组件）

复用性好：`detail` 开关控列集、`onRowClick`/`onEdit`/`onClose` 回调解耦、无权限显「只读」。主控台与持仓页共用同一组件。

**P2 可优化**
- `CoinAvatar` 只给 BTC/ETH 配了品牌色/字符(`PositionsTable.tsx:6-9`)，其余灰底首字母，SOL/XRP/DOGE 只显「S/X/D」辨识度低。**改**：补齐主流币样式表或接图标源，回退用 symbol 前 3 字母。
- 方向列 `p.side === "LONG" ? "mint" : "rose"`(`:79`) 预留做空 rose 分支，但 V0.1 仅现货做多，side 恒 LONG，rose 分支是死代码。**改**：固定 LONG 呈现，去做空分支。
- 12 列窄屏靠 `overflow-x-auto` 横滚（可接受），无移动端卡片化降级，关键列需横拖；低优先。

## M11. 实时事件流展示侧（`stream.ts` / `EventRow.tsx` / `useEvents`）

UI 干净（kind→图标、tone→色、时间戳 mono），WsStream 有指数退避重连 + `event_id` 去重 + `since` 断线回放，底层机制完善。

**P1 应改**
- **前端无连接态/数据新鲜度指示** — 主控台事件流标题「LIVE」是静态 `<Pill tone="mint">LIVE</Pill>`(`Dashboard.tsx:200`)，侧栏「引擎运行中·48ms」写死；WsStream 连接/重连状态从不暴露给 UI。WS 断了照样显「LIVE」。交易监控里「看似实时其实冻结」比「明确显示断线」危险得多——用户会基于过时行情做决策。**改**：WsStream 暴露 `connected/reconnecting`，「LIVE」据此变「重连中…」(amber)/「已断开」(rose)+最后更新时间；侧栏引擎状态同源。
- **事件时间戳 UTC/本地混用** — catchup 路径 `envelopeToEventItem` 用 `occurred_at.slice(11,19)` 直切 UTC(`stream.ts:239`)，实时 mock 用 `nowTs()` 本地，Admin 用本地 `timePart()`，同一屏时间可能差 8 小时。**改**：统一走一个本地时区格式化函数。

**P2 可优化**
- 事件流无「加载更多/查看历史」，只有当日；与审计页同源，一并加时间范围。

---

# 附录 A：守卫预检中文字典（G 类落地用）

前端渲染 `check`（守卫 key）与 `note`（机器串）时套用下表；左标签走字典、右侧通过态显「达标值(限额)」灰字、拦截态显红字一句话原因、原始机器串收进 `title` tooltip。字典建议放 `webapp/src/lib/` 或 `webapp/src/components/market/`，与后端 guard key 对齐。

| 后端 check | 中文标签 | 右侧人话（通过 / 拦截） |
|---|---|---|
| `kill_switch` | 系统急停 | 系统运行中 / **已急停，暂停下单** |
| `daily_loss` | 当日亏损 | 当日盈亏 X%（限 −3%） |
| `consecutive_losses` | 连续亏损 | 近 N 笔连亏（限 3 笔） |
| `balance` | 可用余额 | 需 $X / 可用 $Y |
| `duplicate_position` | 重复持仓 | 无同向持仓 / **已持有该仓** |
| `position_size` | 单仓上限 | 占权益 X%（限 20%） |
| `single_risk` | 单笔风险 | 风险敞口 X%（限 1%） |
| `sl_distance` | 止损距离 | 距离合理 / **止损离入场太远/太近，超出允许区间** |
| `rr_ratio` | 盈亏比 | 1:X（需 ≥ 1.5） |
| `chaotic_regime` | 市场状态 | 状态正常 / **当前混沌行情(CHAOTIC)，禁止开仓** |
| `review` | 复核结论 | 未被否决 / **复核否决** |
| `strategy_enabled` | 策略开关 | 手动单模式 / 策略已启用 |

> 备选：后端在 precheck 响应加 `label`/`message_zh` 由后端下发文案（更彻底、多端一致），但引入后端改动；V0.1 用前端字典最快且零风控耦合。

---

# 附录 B：需后端配合的建议清单

以下建议无法纯前端完成，计划制定时需拆出后端任务：

1. 审计日志/事件流按时间段查询 + 分页（页面 9、模块 M11）
2. 撤单端点（页面 5 WORKING 挂单撤单）
3. 硬风控参数运行期修改端点 `POST /api/config/runtime` + 落审计（页面 7，若选方案 a）
4. 权限授予/撤销端点 + 待批准用户拒绝端点（页面 10）
5. 管理日志/审计记录携带 before-after 变更详情与 resource_id（页面 10、模块 C 类）
6. 原子「紧急停止」端点（先 pause 后 close-all 或事务化）+ 成功/部分失败回执（页面 11、模块 B 类）
7. WsStream 连接态需后端/前端配合暴露（模块 M11，主要前端，但心跳/健康检查依赖后端 `/api/health`）
8. 决策 `decision.progress` 实时阶段事件（模块 M6，让流式动画绑真实守卫状态）
9. Agent pending action 携带具体「键+旧值→新值」透传（模块 M4）
10. Agent 模型分工可配所需 runtime config 字段（页面 11）

（纯前端可独立完成的：A 类假控件改文案/置灰、E 类阈值改读 risk/limits、D 类现货去合约字段/做空、H 类 focus trap/label/aria、I 类动画、G 类守卫字典、决策卡三变体保留 SL/TP、响应式 shell。）
