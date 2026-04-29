# AlphaPilot Mobile UI Kit

iOS 风格可交互原型。5 个核心屏 + 12 个复用组件。

## 屏幕
| 屏 | 路径概念 | 说明 |
|----|---------|------|
| 仪表盘 | `home` | 账户权益 + 收益曲线 + 最新 AI 决策 + 持仓预览 |
| AI 决策流 | `ai` | 时间倒序决策卡片列表，可按"已执行/已拦截"过滤 |
| 持仓 | `pos` | 持仓详情 + SL/TP 可视化轨道 + 平仓操作 |
| 交易日志 | `log` | 审计日志 + AI 日报摘要 |
| 配置中心 | `cfg` | 策略开关 / 硬风控（只读）/ 交易对 / API |

## 组件
- `TopRiskBar` 顶部常驻风控状态条
- `AIDecisionCard` 结构化 AI 决策卡（violet glow hero）
- `DecisionStepper` 决策 → 守卫 → 执行 步进器
- `PositionRow` / `LogRow` / `StatTile` 列表原子
- `Pill` / `Dot` / `Card` / `Num` 基础原子
- `Sparkline` 纯 SVG 收益曲线
- `TabBar` 底部导航

## 场景切换（Tweaks）
通过 Tweaks 面板切换三种市场场景：
- `profit` 盈利 · 风控正常
- `warn` 接近熔断阈值
- `halted` 日亏熔断已触发

## 技术栈
- React 18 + Babel Standalone（原型级）
- 设计 tokens 来自根目录 `colors_and_type.css`
- iOS 设备框来自 `ios-frame.jsx` starter
