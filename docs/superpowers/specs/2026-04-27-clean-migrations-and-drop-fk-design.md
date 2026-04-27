# 清理 Alembic 迁移 + 移除外键约束 — 设计文档

- 日期：2026-04-27
- 作者：Claude（AlphaPilot Phase 3 收尾）
- 状态：待 review

## 背景与问题

### 1. 迁移文件命名混乱

当前 `backend/migrations/versions/` 下共 13 个迁移：

| 一致格式（9 个，`YYYYMMDD_NNNN_*`） | 散乱 hash 格式（4 个） |
|---|---|
| `20260316_0001_init_schema.py` | `d9076875486b_shadow_ops_schema.py` |
| `20260317_0002_add_system_settings.py` | `aa150ff7dee5_extend_ai_decisions.py` |
| `20260317_0003_add_users.py` | `b338184343a4_event_bus_tables.py` |
| `20260317_0004_add_admin_tables.py` | `bbe8a491f942_add_event_outbox_event_id_index.py` |
| `20260421_0001_multi_tenant_accounts.py` | |
| `20260421_0002_factor_schema.py` | |
| `20260421_0003_decision_audit_schema.py` | |
| `20260421_0003a_add_agent_invocations_template_idx.py` | |
| `20260421_0004_insight_schema.py` | |
| `20260421_0004a_add_insight_fk_indexes.py` | |

**根因**：`alembic.ini` 没有配 `file_template`，`alembic revision -m` 默认使用 alembic 自带的 12 位 hash 前缀。

### 2. 数据库定义大量外键

`backend/src/shared/models/*.py` 共有 ~30 个 `ForeignKey(...)` 调用，分布在 21 个 model 文件中。
对应迁移层（init_schema 等 6 个迁移）共建立 ~20 条 FK 约束。

不期望在数据库层维护外键关联，业务在应用层用 ID 关联。

### 3. 当前部署状态

- dev server 尚未部署
- 本地 DB 可随时 drop 重建（无生产数据）
- `relationship(...)` ORM 关系：grep 结果为 0 个，业务确实是手动 join，删 FK 影响面小

## 目标

1. 所有 alembic 迁移文件命名统一为 **`YYYYMMDD_HHMMSS_<rev_hash>_<slug>.py`** 格式（年月日_时分秒_hash_描述）
2. `alembic.ini` 配置 `file_template`，确保后续 `alembic revision -m` 默认产出该格式
3. 数据库 schema 中不存在任何外键约束
4. 模型层 `ForeignKey(...)` 全部删除，列保留为普通 `BigInteger`
5. 单元测试 `make test` 全绿

## 非目标

- 不修改 `relationship(...)` 定义（项目本就没有）
- 不引入业务层 cascade 删除/级联保护机制（后续 issue）
- 不修改业务逻辑里手动 join 的查询（已经是 ID 关联模式）
- 不涉及前端

## 方案

### 命名格式

`alembic.ini` 添加：

```ini
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(rev)s_%%(slug)s
truncate_slug_length = 40
```

产出形如 `20260427_143025_a1b2c3d4e5f6_init_schema.py`。

### 重建策略：方案 α（已确认）

**清空所有现有迁移文件 + drop database + 删除模型层 FK + autogenerate 单一 init 迁移。**

执行步骤：

#### Phase 1 — 清空环境

1. 在 backend 容器内执行 `alembic downgrade base`，把 `alembic_version` 表清掉
2. drop database alphapilot && create database alphapilot（冗余保险，确保 schema 真空）
3. `git rm backend/migrations/versions/*.py`（删全部 13 个旧迁移文件）

#### Phase 2 — 配置 alembic 模板

4. 编辑 `backend/alembic.ini`，在 `[alembic]` 段加 `file_template` 和 `truncate_slug_length`

#### Phase 3 — 删模型层 FK

5. 编辑 `backend/src/shared/models/` 下所有含 `ForeignKey(...)` 的文件：
   - `audit_log.py`、`candle.py`、`decision_review.py`、`attribution.py`
   - `trade.py`、`decision.py`、`agent_invocation.py`、`position.py`
   - `symbol_config.py`、`account_entity.py`、`report.py`、`order.py`
   - `account.py`、`experience.py`、`shadow.py`、`risk_event.py`
   - `prompt.py`、`regime.py`、`factor.py`、`experience_v2.py`、`indicator.py`
6. 删除 `from sqlalchemy import ... ForeignKey` 中的 `ForeignKey` import
7. 把 `mapped_column(BigInteger, ForeignKey("xxx.id"), ...)` 改为 `mapped_column(BigInteger, ...)`
8. 列定义其他属性（nullable / default / index / unique）一律保留

#### Phase 4 — 重新生成 init 迁移

9. 在 backend 容器内执行 `alembic revision --autogenerate -m "init_schema"`
10. 人工 review 生成的迁移文件：
    - 列、索引、唯一约束完整对齐模型
    - 文件内不含任何 `sa.ForeignKeyConstraint(...)` 或 `ForeignKey(...)`
    - PostgreSQL 特定类型（JSON、Numeric 精度）正确
11. 必要时手动调整生成的迁移以匹配预期（如索引命名、`server_default`）

#### Phase 5 — 验证

12. `alembic upgrade head` 把 schema 应用到 dev DB
13. `make test`（53+ tests 全绿）
14. commit + push + `bash scripts/deploy-dev.sh`

### 错误处理

- 如 autogenerate 漏掉某些枚举/索引，手动补齐
- 如某模型字段类型 autogenerate 推断错误（如 `JSON` vs `JSONB`），按原迁移文件的写法修正
- 如 `alembic upgrade head` 失败，回滚提交、分析错误、修正迁移内容（DB drop 重来即可）

### 测试

- 已有 53 passed 单测必须继续通过
- 重点关注：
  - 涉及多表 join 的查询测试（events、decisions、positions）
  - 写入路径的事务测试（FK 删除后不再有数据库层完整性保护）

## 风险与注意事项

| 风险 | 影响 | 缓解 |
|---|---|---|
| autogenerate 与原迁移产出 schema 有差异 | 表结构与测试期望不一致 | Phase 4 步骤 10 人工 review；与原 13 段迁移合并视图比对 |
| FK 删除后业务侧出现孤儿数据 | 数据一致性下降 | 业务层已有 `account_id` 默认值兜底；后续如发现具体场景，单独修；本次不引入 cascade |
| dev DB 还有人在用 | 数据丢失 | dev 未部署，确认无影响 |
| 多人协作时 alembic 链冲突 | 拉代码后冲突 | 本次只有单人推进，git push 后所有协作者按 `make upgrade-db` 即可 |

## 不做的事（YAGNI）

- 不改 `relationship(...)`（项目本就没有）
- 不引入 `ON DELETE CASCADE` 业务侧实现
- 不为遗留 FK 写"drop constraint"迁移（直接整体重建更干净）
- 不 squash 现有 alembic_version 数据迁移（drop DB 即可）

## 验收标准

1. `backend/migrations/versions/` 下只有 1 个文件，命名形如 `YYYYMMDD_HHMMSS_<hash>_init_schema.py`
2. 该文件内无任何 `ForeignKey` / `ForeignKeyConstraint`
3. `backend/src/shared/models/*.py` 中 `grep ForeignKey` 返回 0 条结果
4. `alembic.ini` 含 `file_template` 配置
5. `make test` 全绿
6. dev server 部署成功，前端能正常打开 `/api` 接口
