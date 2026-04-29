# AlphaPilot Design System

面向数字货币市场的 **AI 自主交易系统** 品牌与 UI 设计系统。AlphaPilot 不是"交易建议助手"——它是一个**在明确边界内可自主运行的 AI 数字货币交易平台**。

## 产品上下文

- **产品名**: AlphaPilot（基于 PRD v1）
- **平台**: Binance 数字货币（MVP: BTC/ETH，现货优先）
- **核心能力**:
  - AI 结构化交易决策（OPEN_LONG / CLOSE_LONG / HOLD + 固定 schema）
  - 执行守卫（PASS / REJECT / DEGRADE）与硬风控熔断
  - 市场状态识别（trending_up / trending_down / ranging / chaotic）
  - 经验库沉淀 + 受控进化（Shadow Mode / 自动回滚）
  - AI Trader / Program Trader 双模式路线
- **核心价值四词**: **自主决策 / 风控约束 / 执行闭环 / 受控进化**

## 资料来源

| 类型 | 路径 / 链接 | 说明 |
|------|-------------|------|
| PRD | 用户粘贴 | AlphaPilot 完整产品需求文档（v1） |
| 参考代码 | `github.com/danerlt/Hyper-Alpha-Arena` | 本品牌的前身项目 Hyper Alpha Arena，贡献 tailwind token、图标资产、字体选择（Inter + JetBrains Mono） |
| 参考站点 | `https://www.akooi.com/` | 前身项目官网 |

> ⚠️ 原始 `danerlt/alpha-pilot` 仓库不存在；`Hyper-Alpha-Arena` 是同作者同类产品，已确认用作设计语言参考。

## 目录索引

```
AlphaPilot-Design-System/
├── README.md                  ← 本文件
├── SKILL.md                   ← Agent Skill 入口
├── colors_and_type.css        ← 核心 CSS 变量（颜色/字体/间距/圆角/阴影）
├── assets/                    ← 品牌资产（logo、交易所图标）
│   ├── logo_app.png           ← AlphaPilot 主 Logo（字母 A）
│   ├── arena_logo_app_small.png
│   ├── binance_logo.svg
│   ├── hyperliquid_logo.svg
│   ├── aster_logo.png
│   └── exchange.png
├── preview/                   ← 设计系统预览卡片（供 Design System 标签页）
└── ui_kits/
    └── mobile_app/            ← 移动端 UI Kit（iOS 风格）
        ├── index.html         ← 可交互原型入口
        ├── components/        ← JSX 组件
        └── README.md
```

---

## CONTENT FUNDAMENTALS（文案基本功）

**语言**: 中文为主，英文术语保留（OPEN_LONG / HOLD / PASS / regime / sharpe）。

**人称**: 用"系统"和"AI"替代"我"；与用户沟通用"您"或省略主语。对 AI 行为保持客观描述——"AI 判定"、"守卫拒绝"、"已熔断"，不拟人。

**大小写**: 英文常量全大写（`OPEN_LONG`、`PASS`）；状态词小写（`trending_up`）；标题首字母大写。

**语气**: **严肃、克制、工程化**。不是消费理财产品，是自动化交易基础设施——
- ✅ "日亏 2.1%，触发熔断。已停止新开仓。"
- ❌ "哎呀今天亏了不少哦 😅"

**Emoji 使用**: **禁用**。用图标或色点代替状态。唯一例外：`✓ ✕ !` 作为标记符号可接受。

**数字**: 一律使用等宽字体（JetBrains Mono）；百分比 2 位小数；价格跟随币种精度；盈亏前缀 `+ / −`。

**时间**: `HH:mm:ss` / `MM-DD HH:mm`，不使用相对时间（"3 分钟前"）——金融语境要精确。

**样例文案**:
- 决策卡头: `AI 决策 · BTCUSDT · 15m`
- 风控条: `风控正常 · 今日仓位 12% · 日损 −0.48%`
- 熔断: `日亏 −2.10% ≥ 阈值 2.00% · 已触发熔断`
- 守卫拒绝: `REJECT · 止损缺失 · 决策已回退为 HOLD`
- 复盘: `本日 7 笔交易 · 胜率 57% · 净收益 +1.82%`

---

## VISUAL FOUNDATIONS（视觉基本功）

### 色彩系统
**深色优先**，近黑背景 `#07090F`。核心三色：
- **Mint `#00D395`** — 盈利 / 做多 / 上涨 / 守卫 PASS（源自 Hyperliquid 品牌色）
- **Rose `#FF4D6D`** — 亏损 / 做空 / 下跌 / 守卫 REJECT
- **Violet `#7C5CFF`** — AI 决策、模型输出、经验检索高亮
- Amber `#F0B90B` — 警告 / 降级 DEGRADE / Binance 提示
- Cyan `#22D3EE` — 信息 / 数据流

色彩纪律：涨跌色**不可**作装饰使用，只能用于真实的数值正负。Violet 只出现在 AI 产物上。

### 字体
- `Inter`（无衬线 UI）+ `Noto Sans SC`（中文回退）
- `JetBrains Mono`（所有数字、代码、JSON schema、`trace_id`）
- 无衬线显示字体用于 `ap-display`（账户权益、累计收益这类大数字）

### 背景
- **纯色为主**，不用渐变。
- 允许**极低对比度的网格噪声**（1-2% 不透明度）作为盘面背景纹理——仅限交易大屏区域。
- 光晕（glow）只在关键时刻出现：AI 决策输出时 violet 脉冲；熔断触发时 rose 脉冲；不作装饰。

### 动画
- 曲线 `cubic-bezier(0.4, 0, 0.2, 1)`；时长 160–300ms。
- 数字变化用翻页 / 色闪动画（参考源项目 `flip-digit` / `number-up`）。
- 状态切换用 fade + 微位移；不用弹跳。
- 实时数据更新允许 `highlight-flash` 高亮 1 次。

### 交互状态
- **Hover**: 背景提升一级（`bg-2` → `bg-3`），不改变颜色相位。
- **Press**: `scale(0.98)` + 背景再提一级。
- **Focus**: `1.5px` ring（violet 或 mint）。
- **Disabled**: 透明度 40%，不变灰。

### 边框与分隔
- Hairline `1px` `#222838`。极少使用粗边。
- 卡片之间用间距分隔而非边框；同一卡片内用 `#1A1F2B` 细分隔线。

### 阴影
- 三档：`shadow-1`（微）、`shadow-2`（浮层）、`shadow-3`（弹窗）。深色模式下阴影**仍要用**——半透明黑 + 距离感。
- **Glow** 阴影专用于状态：mint-glow / rose-glow。

### 透明度与模糊
- 顶栏与底栏使用 `backdrop-filter: blur(20px)` + 半透明 `#0B0E15CC`，iOS 质感。
- 模态遮罩 `#000000B3`。

### 圆角
- 卡片 `12–16px`，按钮 `10–12px`，Pill 标签 `999px`，输入框 `10px`。统一且克制。

### 布局
- 移动端 `16px` 左右边距；内容最大 `428px`（iPhone 16 Pro Max）。
- 顶栏固定 56px；底栏 Tab Bar 72px（含 home indicator）。
- 卡片内部 `16px` 内边距；卡片间 `12px` 间距。

### 卡片规范
- 背景 `--ap-bg-2`，圆角 `16px`，无描边（或 `1px #1A1F2B`）。
- 内部层级用背景颜色深浅区分，不用线。
- 强调卡片（AI 决策、熔断）可带 1px violet/rose 发光描边。

### 图像色调
- 截图配图走冷色 / 低饱和；K 线用纯色填充（mint 阳 / rose 阴）。
- 无真人照片。品牌叙事靠数据与符号。

---

## ICONOGRAPHY（图标）

- **主图标库**: [**Lucide**](https://lucide.dev)（源项目 `lucide-react` 0.536.0），1.5px 描边，圆角。通过 CDN 加载：
  ```html
  <script src="https://unpkg.com/lucide@latest"></script>
  ```
- **Emoji**: **禁用**。以 Lucide 图标或彩色圆点替代。
- **Unicode 符号**: 允许极少数功能性符号：`↑ ↓ → · • ◆ ●`。
- **交易所 Logo**: 来自源项目：
  - `assets/binance_logo.svg` — Binance 菱形钻石
  - `assets/hyperliquid_logo.svg` — Hyperliquid 波浪 H
  - `assets/aster_logo.png`
- **应用 Logo**: `assets/logo_app.png` — 大写字母 A，简洁几何造型（可作 favicon / 启动图）。
- **自绘 SVG**: 仅用于业务特异图形（如 regime 状态图示、决策流节点）。

### 典型图标用途
| 场景 | Lucide 名 |
|------|-----------|
| 仪表盘 | `layout-dashboard` / `gauge` |
| AI 决策 | `brain` / `sparkles` |
| 持仓 | `wallet` / `coins` |
| 交易日志 | `scroll-text` / `activity` |
| 风控 | `shield` / `shield-alert` |
| 策略 | `settings-2` / `sliders` |
| 熔断 | `octagon-x` / `zap-off` |
| 复盘 | `line-chart` / `book-open` |
| 趋势上/下 | `trending-up` / `trending-down` |

---

## 字体替换声明

源项目使用 **Inter** 与 **JetBrains Mono**，两者均在 Google Fonts 可用，**无替换**。中文补充 **Noto Sans SC**（同为 Google Fonts）。

---

## 下一步 / 共创请求

这是基础版设计系统 v0.1。欢迎在以下方向迭代：
1. 确认三色分工（mint/rose/violet），或换成其他品牌方向
2. 提供真实 AlphaPilot Logo（当前沿用参考项目的字母 A logo）
3. 是否加入 Program Trader / 因子库相关的专属图形语言
4. 确认是否保留禁用 emoji 的规则
