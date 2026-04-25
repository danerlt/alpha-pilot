# 2026-04-25 — Plan 2-5 累计代码审查（subagent code-reviewer）

## 范围

git range: `f70f0a0..7294b62`，~34 commits，132 文件改动，+9766 / -867 行。
覆盖 Plan 2 (Trading Loop) / Plan 3 (Control) / Plan 4 (Frontend DS) /
Plan 5 (调度切换 + WebSocket + router 拆分)。

## Strengths（值得保留）

- 四平面边界清晰：Insight / Strategy / Execution / Control 物理隔离, DecisionProposal 是唯一跨平面契约
- fallback HOLD 通路完整: `proposal.fallback_hold` + DecisionSolver 兜底 + Pipeline 全异常落 HOLD, ai_decisions 行带 raw_output 可回放
- trace_id 幂等设计扎实: OrderExecutor.make_trace_id + InboxGuard SAVEPOINT + OutboxWriter 同事务写入
- ExecutionGuard 全审计: PASS/REJECT/DEGRADE 都写 risk_events
- USE_NEW_PIPELINE_WORKER feature flag 切换显式, 旧路径完整保留可回滚
- schema 增量为零: BigIntPk 用 with_variant 让 SQLite 兼容, Postgres 仍 BIGINT, 完全 backwards-compatible
- 测试覆盖纵深: 342 passed, unit + testcontainers 两层

## Critical（阻塞 V0.1 部署，必须修）

| # | 问题 | 位置 | 修法 |
|---|------|------|------|
| C1 | `commands.py` 完全无 JWT 校验, `_operator_user_id() return 1` 是 backdoor | `routers/commands.py:66-68` | 改成 `Depends(require_admin)` |
| C2 | 所有查询 API 无鉴权, 交易策略 / PnL / AI 决策推理裸奔 | `routers/{positions,trades,decisions,risk,reports,account}.py` | 加 `Depends(get_current_user)` |
| C3 | `positions.py` 的 close 端点和 `commands.py` 重复且行为冲突 (旧版不写 audit / 无 confirmation) | `routers/positions.py:44-65` vs `routers/commands.py:71-85` | 删 positions 的 close 端点, 统一走 commands |
| C4 | WebSocket 不验 token + catchup 协议错位 (前端拼 since, 后端从未读) | `app/websocket.py:47-57`, `frontend/lib/ws.ts:56` | 服务端在 accept 前验 token, 握手后用 since 触发 outbox 回放 |

## Important（应该修，V0.1.1 跟进）

| # | 问题 | 位置 |
|---|------|------|
| I1 | 26 个事件契约只 publish 5 类: IndicatorsComputed/FactorsUpdated/RegimeClassified/ProposalDrafted/DecisionProposed/DecisionReviewed/DecisionDegraded/DecisionRejected 全无发布. 要么标注 V0.1 子集, 要么 strategy_pipeline 各阶段补 publish | `strategy_pipeline.py`, `events/contracts.py:7-9` |
| I2 | 熔断检查两处实现 (KillSwitch + `_circuit_breaker_active`), position_monitor_worker 没接 KillSwitch | `scheduler_jobs.py`, `strategy_pipeline.py:55-72` |
| I3 | `run_strategy_pipeline_once` 198 行函数, 内嵌 import, 拆 `_run_one_symbol_tf()` | `strategy_pipeline.py` |
| I4 | DecisionId 取 `order_by id desc limit 1` 不可靠, AITraderPipeline 已返回 decision_id 但未传出 | `strategy_pipeline.py:253-275` |
| I5 | PromptComposer trading_mode 硬编码 testnet, mainnet 时 ProposalDraft.trading_mode 错误 | `prompt_composer.py:115` |
| I6 | FactorComputer / RegimeClassifier delete-then-insert 并发不安全 (V0.1 单 worker OK), Postgres 应换 ON CONFLICT | `factors/computer.py:59-67`, `regime/classifier.py:112-120` |
| I7 | 新 worker 无 unit test (strategy_pipeline / scheduler_jobs / position_monitor_worker 只在集成层覆盖) | `backend/tests/unit/workers/` 缺失 |
| I8 | 9 个新 router 函数体内 import (拆分时图省事), 应挪顶部 | `routers/{positions,trades,decisions,...}.py` |
| I9 | frontend `apiRequest` 401 时不触发登出/重定向 | `lib/api.ts:20-31` |
| I10 | EventShuttle 死信 publish 失败会无限重试 + MAX_FAILED_ATTEMPTS=3 神奇数字 | `event_shuttle.py:28, 99` |
| I11 | Guard 不发 DecisionDegraded / DecisionRejected 事件契约, Notifier 拿不到 degrade 信号 | `execution_guard.py:162-172` |

## Minor（锦上添花）

- `_aware()` SQLite tz 兼容逻辑在多处重复, 抽到模块级 util
- `_build_adapter` 在 commands / scheduler_jobs / 旧 positions 各自构造, 应统一到 dependencies.get_adapter
- `MAX_FAILED_ATTEMPTS / CATCHUP_LIMIT_HARD_CAP / MAX_POSITION_SIZE_PCT_HARD_CAP` 等神奇数字汇总到 shared/constants.py
- `RegimeSnapshot.factor_snapshot_id` 列 Plan 5 仍未补, 影响 V0.2 attribution
- 旧 `workers/strategy_loop.py` 在 USE_NEW_PIPELINE_WORKER=true 时变死代码, Plan 5 完整切完后删除
- frontend lib/api.ts commands 形状手写, 建议 OpenAPI codegen
- `_extract_bearer_token` 下划线开头但被外部依赖, 改名

## V0.1 部署前最少修复清单

按上面 Critical 4 项逐一修, 工作量约：

1. C1+C2 加鉴权: ~10 行修改 (每个 router 文件加 Depends(get_current_user) 或 require_admin)
2. C3 删 positions 重复端点: ~25 行删除 + frontend 改 URL
3. C4 WebSocket 鉴权 + catchup 实现: ~50 行 (token 验证 + since 参数读取 + outbox XRANGE 回放)

预估 1-2 个工作时即可清零 Critical, 之后 V0.1 可上 Testnet 验收。

## 后续 PR 计划

- **PR-A (V0.1 阻塞修复)**: C1+C2+C3+C4
- **PR-B (V0.1.1 健壮性)**: I1+I2+I4+I5+I7
- **PR-C (cleanup)**: I3+I8+I10 + Minor 项

完整审查记录见 chat history; 对应 commits f70f0a0..7294b62.
