# IMPLEMENTATION_PLAN — 前端现代化 P0→P5（全自动执行）

> 设计依据：`docs/superpowers/specs/2026-06-28-frontend-modernization-design.md`
> 全部完成后删除本文件。每期全绿才提交推送。

## 阶段 P0: 地基（纯前端，零行为改动）
**目标**: 令牌单一化 + 组件库 + 左侧栏 shell + Modal/事件总线基础设施
**成功标准**: build + tsc + vitest 全绿；所有路由在新 shell 下行为不变；无蓝紫/发光球/渐变；数字 mono；后端零改动
**子步骤**:
- [完成] 令牌清理（globals.css 别名 → --ap-*；删发光球/渐变 body；layout 去 ambient div）
- [完成] 引入 lucide-react + Icon 封装
- [完成] 组件库 src/components/ui/（Button/Card/StatCard/Badge/Table/RiskBanner/Modal/ConfirmDialog/Dot/Sparkline）+ 14 单测；vitest 接入 plugin-react
- [完成] 新 shell：Sidebar(240px 品牌/权益/8段导航/引擎状态/登出) + Topbar(风控胶囊降级版/AUTO/通知红点) 替换 app-shell；窄屏抽屉
- [完成] 危险操作 ConfirmDialog 基础设施（含 requireText 口令校验）
- [范围微调→P1] 事件总线 Provider 随其消费方(dashboard)在 P1 落地；dashboard 内残留 emoji 随 P1 重做清除
**状态**: 完成（build + tsc + vitest 33 passed 全绿）

## 阶段 P1: 拆页 + 主控制台重做（纯前端，现有接口）
**目标**: 1060 行单页拆成 8 段路由；主控制台 = AI 决策 hero(Stepper) + 权益卡 + 关键指标 + 持仓预览 + 实时事件流
**成功标准**: 高危写操作契约全保 + admin 边界不变 + 前端单测；build/tsc/vitest 绿
**状态**: 未开始

## 阶段 P2: 能力页铺满（纯前端，现有接口）
**目标**: 决策流/持仓与订单/交易与绩效/策略与风控/归因与审计/设置/管理后台换皮；/admin/currencies→/admin/symbols + 重定向
**状态**: 未开始

## 阶段 P3: 后端三小改解锁视觉亮点（后端+前端）
**目标**: 扩展 /api/decisions 字段；新增 GET /api/orders、GET /api/account/history；(可选) GET /api/risk/state；前端接入决策卡字段网格/订单簿/权益曲线/风控胶囊
**成功标准**: pytest + ruff + 前端三件套全绿；读现有表预计无 alembic 迁移
**状态**: 未开始

## 阶段 P4: AI 决策深度可视化（中工程）
**目标**: GET /api/decisions/{id}/guards + /features → Graph/Timeline 决策卡变体；AI 日报叙述(attribution.narrative 过渡→LLM)
**状态**: 未开始

## 阶段 P5: 绩效/回测引擎 + 策略启停（大工程）
**目标**: 回测 vs HODL / 账户级 Sharpe·Sortino / 盈亏比；策略级 enabled 开关（alembic 迁移走 revision 命令）
**状态**: 未开始
