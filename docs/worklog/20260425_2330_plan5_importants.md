# 2026-04-25 — Plan 5 Important 11 项收口

## 范围

接续 `20260425_2200_plan5_codereview.md` 列出的 11 项 Important，按
"PR-B 健壮性跟进" 的批次推进，对应 commit 区间约
`8c165fd..502ee5f` (10 commits)。

## 完成清单

| # | 内容 | 关键 commit |
|---|------|------------|
| I4+I5 | AITraderPipeline 透传 decision_id, PromptComposer 接收 trading_mode | `1f3a898` |
| I1 | strategy_pipeline 关键阶段补 publish + contracts 文档化 V0.1 子集 | `bc9d1cb` |
| I2 | KillSwitchService 新增 has_unresolved_circuit_breaker / should_block_new_trades, 替代 worker 私有 _circuit_breaker_active | `dfff769` |
| I3 | 拆 run_strategy_pipeline_once 主体到 _run_one_symbol_tf, 引入 _PipelineDeps | `e207acf` |
| I6+I8 | router 顶层 import 清理 + Factor/Regime UPSERT 单写假设文档化 | `42ac7e6` |
| I11 | ExecutionGuard DEGRADE/REJECT 时发布 decision.degraded/rejected | `edec7c7` |
| I10 | EventShuttle 死信策略 (失败兜底) + MAX_FAILED_ATTEMPTS 改可配 | `2dad13c` |
| I7 | scheduler_jobs / position_monitor_worker 单元测试 (8 用例) | `635742c` |
| I9 | 前端 apiRequest 401 自动 clearStoredSession + 跳 /login?reason=session_expired | `502ee5f` |

## 测试演进

```
Plan 5 Critical 完成     → 327 passed (8c165fd 排除 docker 集成层)
I4+I5 完成              → 327 passed
I1   完成              → 332 passed (+5 outbox publish 用例)
I2   完成              → 342 passed (+9 KillSwitch + 1 pipeline)
I3   完成              → 342 passed (纯重构无新增)
I6+I8 完成              → 342 passed (文档化 + import 整理)
I11  完成              → 347 passed (+5 Guard publish)
I10  完成              → 353 passed (+6 EventShuttle 单测)
I7   完成              → 361 passed (+8 worker 单测)
I9   完成              → 361 passed (前端无可执行测试)
```

排除的 7 个集成测试都是 testcontainers 依赖 (docker), 本机环境没启动；
本地 sqlite 路径全部跑通。

## 关键设计决策

1. **decision_id 改为 pipeline 主输出**
   `AITraderPipeline.run` / `StrategyRouter.decide` 改返回
   `(DecisionProposal, decision_id|None)` 元组, 让 worker 不再做
   `AIDecision.order_by(id.desc()).limit(1)` 反查 — 反查在并发 / 多
   strategy 场景不可靠。decision_id=None 表示在 Solver 阶段前就回退。

2. **trading_mode 沿全链路透传**
   PromptContext 增加 trading_mode 字段并参与 canonical_json,
   保证 testnet/mainnet 的 ProposalDraft + context_hash 隔离, 不会跨环境串.

3. **KillSwitch 单一阻塞口径**
   should_block_new_trades = is_paused OR has_unresolved_circuit_breaker;
   strategy_pipeline 只问一个开关; position_monitor 不接 KillSwitch
   保持 SL/TP 永远跑. scheduler_jobs.new_strategy_pipeline_job 仍保留
   is_paused 早期 short-circuit 节约连接.

4. **EventShuttle 死信兜底**
   原版 dead_letter publish 失败时不标 published_at, 会无限循环重试,
   现在无论 dead_letter 成功失败都标 published_at + last_error 留存
   `dead_letter_failed:...` 后缀方便排查; payload_json 仍在 outbox
   表可手动重放.

5. **V0.1 publish 子集显式文档化**
   contracts.py 头注列出实际发布的 16 类事件 vs V0.1.1+ / V0.3+ 仍占位
   的契约, 让 codereview 提的 "26 类只发 5 类" 有据可查; 实际现在已
   publish 14 类 (含 I11 加的 decision.degraded/rejected).

## 下一步

V0.1 部署前剩余动作 (老板执行):

1. SSH 到 dev server 跑 `bash scripts/deploy-dev.sh` — 本机不持有
   `.env.dev-server`, 按 CLAUDE.md "禁止主动读真实 env 文件"规则
   不能代办。脚本会自动 `git pull` + 重建镜像 + 跑 alembic 迁移。
2. 部署完观察 7 天 Testnet 连续运行 (Plan 5 codereview 提到的部署
   验收标准).
3. V0.1.1 跟进项: PromptComposer 暴露 draft_id / ReviewCritic 暴露
   review_id 后, 在 worker 补 publish proposal.drafted +
   decision.reviewed; KillSwitch / Commands 路径补 publish
   circuit_breaker.triggered + control.command (V0.1.1 codereview 列表
   完整版见 contracts.py 头注).

## 对应主要 commit

```
1f3a898  plan5(I4+I5) AITraderPipeline 透传 decision_id
bc9d1cb  plan5(I1)    strategy_pipeline 补发 4 类策略阶段事件
dfff769  plan5(I2)    KillSwitchService 统一阻塞口径
e207acf  plan5(I3)    拆分 run_strategy_pipeline_once
42ac7e6  plan5(I6+I8) router 顶层 import + Factor/Regime 单写文档
edec7c7  plan5(I11)   Guard 发布 decision.degraded/rejected
2dad13c  plan5(I10)   EventShuttle 死信策略 + max_attempts 可配
635742c  plan5(I7)    scheduler_jobs / position_monitor_worker 单测
502ee5f  plan5(I9)    前端 apiRequest 401 自动登出 + 跳转 /login
```
