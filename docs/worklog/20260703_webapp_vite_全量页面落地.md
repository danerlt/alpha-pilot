# 2026-07-03 · webapp（Vite 新前端）全量页面落地

## 做了什么

按老板指令（React 18 + Vite + TypeScript + Tailwind + mock API 层）基于
`AlphaPilot Design System/handoff/` 交付包，在仓库新建 **`webapp/`** 独立前端应用，
一次性落地 shell + 全部 11 个页面。**未触碰现有 Next.js `frontend/`**（生产 CI 仍挂它，可随时回退/并行演进）。

### 技术底座

- Vite 5 + React 18 + TS strict + Tailwind 3（`tailwind.config.ts` 只做 `var(--ap-*)` 变量映射，业务代码零硬编码色值）
- token 权威源 `colors_and_type.css` 全量拷入 `src/styles/design-system.css`
- API 层：`src/api/types.ts`（handoff/03 全部契约的 TS 类型）+ `src/api/services.ts`
  （每个 service 双实现：`VITE_API_BASE_URL` 未配置走 mock，配置后无缝切真后端）
- 图标 lucide-react；数字全 JetBrains Mono + tabular-nums；禁 emoji；中文为主保留英文技术词

### 页面清单（对照 handoff/02）

| 页面 | 路由 | 关键实现 |
|------|------|----------|
| shell | — | Sidebar 240px（品牌/权益/10 段导航/引擎状态/用户卡）+ Topbar（风控胶囊 WS 位/CtrlK/Pilot AI/通知红点/AUTO）+ CommandPalette + ChatDrawer(CtrlJ) |
| 主控制台 | `/` | HaltBanner + AI hero（StreamingDecision 五段点亮+重放）+ 权益卡（AnimatedNumber/SparkLive 十字光标）+ 4 磁贴 + 持仓预览 + 实时事件流；HALTED 五件套联动 |
| 行情 | `/market` | 自选 220px｜K线（SVG 蜡烛+量能+SL/TP/入场标线钉边缘+现价 cyan 虚线+OHLC tooltip）｜AI 解读条｜OrderTicket（守卫预检走 API、HALTED 仅 Reduce-Only）+ 盘口/成交 + 市场信息 |
| AI 决策流 | `/decisions` | 过滤 tab + 三变体卡（stepper/timeline/graph，localStorage 记忆）+ 首条流式重放 + 详情弹窗（features/守卫逐项/reasoning/关联订单） |
| 持仓与订单 | `/positions` | 4 磁贴 + 全列持仓表（编辑 SL/TP 走预检、平仓二次确认）+ 订单簿 + 空态 |
| 回测与绩效 | `/performance` | 6 磁贴 + 策略 vs HODL 曲线 + 月度 PnL 零轴柱图 + 交易统计 + 归因维度切换 |
| 策略与风控 | `/risk` | 策略受限集（启停走 ConfirmDialog）+ 硬风控只读表 + 交易对管理 |
| 策略实验室 | `/lab` | 受控进化流水线图示 + 候选卡（影子进度/逐项对比标▲/门槛禁用说明）+ 进化历史 |
| 审计日志 | `/audit` | 事件流全量 + 类型过滤 + AI 日报卡 |
| 设置 | `/settings` | 四分区：交易所（主网 rose 警告/测试网 cyan、密钥脱敏、权限校验清单）/ LLM（提供方选卡/温度滑块/Agent 分工）/ 通知 / 账户（紧急停止输 STOP 确认） |
| 后台管理 | `/admin` | 用户管理（pending 批准）+ 角色权限矩阵（Owner 列锁定）+ 管理日志 |
| 登录 | `/login` | 左品牌面板 + 登录/注册（pending 提示）/ 2FA 六位逐格自动跳格自动提交 |

## 为什么做

- 老板本次指令明确指定 Vite 新栈 + mock 先行；按 handoff/00 冲突优先级（老板指示最高）执行
- 交接包 01/04 原写的是落进 Next.js `frontend/`——两条线并存，后续由老板定去留

## 如何验证

- `cd webapp && npm run build`（tsc --noEmit + vite build）全绿
- dev server 起于 5173，11 个路由逐页 DOM 走查：token（bg-0 #07090F）、JetBrains Mono、
  各页关键区块全部在位；行情页蜡烛/量能渲染 138 个 SVG 元素
- 后端单测由 pre-commit 钩子全量通过（webapp 为纯前端新增，后端零改动）

## 对应 commit

- `281cca2` 脚手架 + 设计系统底座 + shell + 主控制台
- `a5403bf` 行情页
- `542a2f0` AI 决策流页 + 持仓与订单页
- `02edbf3` 设置页四分区
- （本次）绩效/风控/实验室/审计/后台/登录 + worklog

## 遗留

- WS 实时驱动（risk.state/decision.progress/event.append）目前为 mock 静态数据，后端就绪后接 `/ws` 即可
- K线生产建议换 lightweight-charts（当前 SVG 自绘已满足像素稿）
- webapp 尚未接部署管线（docker/CI 仍指 frontend/），等老板定两条前端线的去留
