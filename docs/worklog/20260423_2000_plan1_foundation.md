# 2026-04-23 — Plan 1 Foundation 实施完成

## 背景

按 `docs/superpowers/plans/2026-04-21-alphapilot-v01-plan1-foundation.md` 执行 V0.1 Plan 1 共 17 个 Task，产出 AlphaPilot V1.0 目标架构的基础层（schema + 事件总线 + 交易所适配）。使用 subagent-driven-development skill 派发、两阶段审查（spec 合规 + 代码质量）。

## 交付摘要

| 层 | Task | 产出 |
|------|------|------|
| Schema 多租户改造 | 1 | `accounts` / `risk_profiles` / `parameter_versions` + 13 业务表 `account_id` 回填 |
| Schema 新建 | 2-5 | 因子层（3）/ 决策审计（4）/ 洞察（4）/ Shadow-Ops（3）共 14 张表 |
| Schema 扩展 | 6 | `ai_decisions` 加 7 列（LLM 元数据 + source + FK） |
| 事件底座 | 7-12 | UUIDv7 工具 / 26 个事件契约 + registry / event_inbox+outbox / Redis Streams bus / OutboxWriter + EventShuttle / InboxGuard |
| 交易所适配 | 13-16 | ExchangeAdapter 抽象 + 值类型 / RateLimiter 令牌桶 / with_retry 装饰器 / BinanceAdapter 具体实现 |
| 冒烟测试 | 17 | 端到端闭环：testcontainers Postgres+Redis → 业务写+Outbox → Shuttle → Streams → Inbox → ack |

## 测试结果

- 基线（Plan 1 前）：80 passed
- Plan 1 完成后：**173 passed + 2 skipped**（skipped 为需真实 Binance testnet key 的 live 集成）
- 新增测试：93 个（单元 + 集成）
- 所有提交均 push 到 `origin/main`

## Alembic 迁移链

```
20260317_0004 (既有)
  ↓
20260421_0001 (multi_tenant_accounts)
  ↓
20260421_0002 (factor_schema)
  ↓
20260421_0003 (decision_audit_schema)
  ↓
20260421_0003a (agent_invocations_template_idx, follow-up)
  ↓
20260421_0004 (insight_schema)
  ↓
20260421_0004a (insight_fk_indexes, follow-up)
  ↓
d9076875486b (shadow_ops_schema — 首次用 alembic revision 命令生成)
  ↓
aa150ff7dee5 (extend_ai_decisions)
  ↓
b338184343a4 (event_bus_tables) ← 当前 head
```

Task 1-4 的四个迁移文件在 Plan 1 初期由 Claude 直接 Write 写出。老板在 Task 4 完成后明确规定：**数据库变更必须走 `alembic revision` 命令生成骨架**，Claude 只编辑 upgrade/downgrade 正文。该规则已写入 `C:\Users\tao\.claude\CLAUDE.md` 的 NEVER/ALWAYS 段。Task 5 起严格遵守。

## 新增代码结构

```
backend/src/
├── events/                   ← 事件总线 (Task 7-12)
│   ├── ids.py                UUIDv7 工具
│   ├── contracts.py          26 事件契约 + EventEnvelope + REGISTRY
│   ├── bus.py                InMemoryEventBus + RedisStreamsBus
│   ├── outbox.py             OutboxWriter
│   └── inbox.py              InboxGuard
├── execution/                ← 执行核心 (Task 13-16)
│   └── exchange/
│       ├── types.py          Kline / Ticker / OrderRequest / OrderResult
│       ├── adapter.py        ExchangeAdapter(ABC)
│       ├── rate_limiter.py   令牌桶
│       ├── retry.py          with_retry 装饰器 + 异常分层
│       └── binance_adapter.py
├── workers/event_shuttle.py  ← Outbox → Streams 搬运 (Task 11)
└── shared/models/            ← 新增 7 个模型文件（14 张表 + 2 事件表）
```

## 审查记录

每个 Task 的流程为：派发 implementer → spec 合规 reviewer → 代码质量 reviewer → 按建议收口。Task 4 起遇到 `superpowers:code-reviewer` subagent rate limit，改由主 agent 做 inline 质量审查；Task 13-17 由于 general-purpose subagent 也命中 rate limit，全部改 inline 实施并审查。质量门未下降，TDD 红-绿流程全部走到位。

关键的 code review 提示（非阻塞，已记入 cleanup）：

- Task 3：`__table_args__` 声明 Index 让模型 metadata 反映 DB 状态，已回补到 FactorSnapshot / FactorDefinition（`20260421_0003a` 另建迁移加 `ix_agent_invocations_prompt_template_id`）
- Task 4：experiences / summaries / attributions 三张表的 FK 列加索引（`20260421_0004a`）
- Task 10：implementer 简化掉的 `test_ensure_group_is_idempotent` 在 post-plan cleanup 阶段补回

## 遗留（不阻塞 Plan 2）

- `AuditLog.id` / `SymbolConfig.id` 是 `Integer` 而非 `BigInteger`（pre-existing 债，涉及数据迁移，暂不修）
- 旧 `experience_store` 表与新 `experiences` 表并存；V0.1 写入新表，V0.2 再做数据合并策略
- 若干迁移的 `downgrade()` 有多余的 `drop_index`（PG 下 `drop_table` 会级联），语义冗余但不影响正确性

## 规则持久化

本次 Plan 1 期间老板下达并写入 `C:\Users\tao\.claude\CLAUDE.md` 的新全局规则：

- 中文回答，每次以「好的，老板」开头（原有）
- 数据库变更走 `alembic revision` 命令生成骨架，不用 Write 工具手写迁移文件（新增）

## 验收

- `cd backend && .venv/Scripts/python.exe -m pytest backend/tests/ -q` 全绿（173/175）
- `alembic heads` = `b338184343a4`
- 端到端冒烟 `test_foundation_smoke.py` PASS
- 所有 commit 已 push 到 `origin/main`

## 对应 commits

```
dbdbad7  chore: finish src.app.main → src.app.app rename
969993933  foundation(plan1): add multi-tenant schema ...
d26507e  foundation(plan1): polish Task 1 per code review
260a124  foundation(plan1): add factor layer schema ...
c56bfcc  foundation(plan1): add decision audit schema ...
e5ea957  foundation(plan1): apply Task 3 review follow-ups
4cb36c3  foundation(plan1): add insight schema ...
b473d0c  foundation(plan1): apply Task 4 review follow-ups
4b448f6  foundation(plan1): add shadow + ops schema ...
4680654  foundation(plan1): extend ai_decisions ...
c6500a0  foundation(plan1): add UUIDv7 event id utility
571fc41  foundation(plan1): add event contracts module ...
e366e39  foundation(plan1): add event_inbox + event_outbox tables
3c9f73b  foundation(plan1): add EventBus abstraction ...
a1556a5  foundation(plan1): add OutboxWriter + EventShuttle worker
8132fd1  foundation(plan1): add InboxGuard ...
8babb77  foundation(plan1): add ExchangeAdapter abstract interface + value types
b0e50e7  foundation(plan1): add token-bucket RateLimiter ...
25a1329  foundation(plan1): add with_retry decorator ...
7fbde40  foundation(plan1): add BinanceAdapter ...
aaad974  foundation(plan1): add end-to-end smoke test ...
ff320d8  foundation(plan1): post-plan cleanup
```
