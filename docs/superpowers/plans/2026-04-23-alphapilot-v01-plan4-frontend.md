# AlphaPilot V0.1 Plan 4 — Frontend (Design System 对齐)

**Goal:** 把 `AlphaPilot Design System/` 的视觉规范、颜色变量、Web Shell 全套搬进 `frontend/`；按 DS 规定的 7 页路由组织 Dashboard / AI 决策流 / 持仓与订单 / 回测与绩效 / 策略与风控 / 审计日志 / 设置；接 Plan 3 commands API + WebSocket 实时更新。

**Architecture:** Next.js 14 App Router + DS atoms 单层抽象 (`components/ds/`) + 业务组件层 (`components/domain/`)。色彩走 CSS 变量；数字 JetBrains Mono；禁用 emoji；危险操作二次确认。

**Tech Stack:** Next.js 14, React 18, TypeScript, lucide-react (Icon), DS 自定义 CSS 变量。

---

## File Structure

```
frontend/src/
├── styles/
│   └── design-system.css          ← 复制 AlphaPilot Design System/colors_and_type.css
├── components/
│   ├── ds/                         ← DS atoms (TypeScript)
│   │   ├── shell/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Topbar.tsx
│   │   ├── atoms/
│   │   │   ├── Card.tsx Stat.tsx Pill.tsx Dot.tsx Spark.tsx Icon.tsx
│   │   ├── cards/
│   │   │   ├── AIDecisionCard.tsx
│   │   │   ├── RiskBannerCard.tsx
│   │   │   └── PositionRowCard.tsx
│   │   └── format.ts                wfmt / wfmtPct / wfmtSigned
│   └── domain/
│       ├── AccountSummary.tsx
│       ├── OpenPositionsTable.tsx
│       └── DecisionFeed.tsx
├── lib/
│   ├── api.ts                      REST 客户端
│   ├── ws.ts                       WebSocket 重连 + catchup
│   └── format.ts                   一致的数字/价格/百分比格式化
└── app/
    ├── (public)/
    │   ├── login/page.tsx
    │   └── register/page.tsx
    └── (app)/
        ├── layout.tsx              ← Web Shell + RouteGuard
        ├── page.tsx                Dashboard (7 页之 1)
        ├── ai/page.tsx             AI 决策流
        ├── positions/page.tsx
        ├── performance/page.tsx
        ├── risk/page.tsx
        ├── audit/page.tsx
        └── settings/page.tsx
```

---

## Tasks (精简版，每个 Task 含核心组件 + 页面)

### Task 1: design-system.css + Lucide Icon
- 把 DS 的 colors_and_type.css 复制到 `frontend/src/styles/design-system.css`
- 在 `app/layout.tsx` 顶部 import; 设 body 默认走 var(--ap-bg-0)
- 装 `lucide-react`; 写 `components/ds/atoms/Icon.tsx` 包装

### Task 2: DS atoms — Card / Stat / Pill / Dot / Spark
- 从 `AlphaPilot Design System/ui_kits/web_app/components/shell.jsx` 抽出 5 个 atom 转 TypeScript
- 写最小化的 props + tone (mint/rose/violet/amber/cyan/default)

### Task 3: Web Shell (Sidebar + Topbar + AppShell)
- `components/ds/shell/Sidebar.tsx`: 240px 侧栏 + 7 项导航 + 引擎状态 + 账户权益
- `components/ds/shell/Topbar.tsx`: 60px 顶栏 + 风控胶囊 + 搜索 + 通知 + AUTO 开关
- `components/ds/shell/AppShell.tsx`: 组合 Sidebar + Topbar + content slot

### Task 4: AIDecisionCard (3 variants)
- `components/ds/cards/AIDecisionCard.tsx`: 接受 `variant: 'stepper'|'timeline'|'graph'`
- V0.1 默认 stepper; timeline / graph 留出占位

### Task 5: 业务 hooks 与 lib (api.ts + ws.ts)
- `lib/api.ts`: REST 客户端, 接 Plan 3 commands + 既有 router
- `lib/ws.ts`: WebSocket 自动重连 + catchup (?since=)

### Task 6: Dashboard 页 (主控制台)
- 路由 `app/(app)/page.tsx`
- 组件: EnvironmentBanner + Hero AI 决策卡 + Equity Sparkline + 关键指标 + Open Positions Table + Events Feed
- 接 WebSocket 实时更新

### Task 7: 其他 6 页（最小可访问骨架）
- `/ai`、`/positions`、`/performance`、`/risk`、`/audit`、`/settings` 各一个页面
- 内容是 placeholder + DS atoms 组合，确保导航可用

### Task 8: 危险操作二次确认对话框
- `components/ds/cards/DangerConfirmDialog.tsx`: 一键全平要求输入 `CLOSE ALL`; 解除熔断要求输入 `UNLOCK`
- 集成到 `/risk` 页和顶栏 KillSwitch 按钮

---

## 自检清单

- [ ] `npm run build` 零错误零警告
- [ ] 所有路由可访问 (7 页 + 登录注册)
- [ ] 色值无硬编码 #00D395 等; 全部 var(--ap-mint) etc.
- [ ] 数字字体 JetBrains Mono
- [ ] 危险操作有二次确认
- [ ] WebSocket 自动重连可见
