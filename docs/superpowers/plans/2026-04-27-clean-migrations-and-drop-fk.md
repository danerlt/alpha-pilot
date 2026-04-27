# Clean Alembic Migrations + Drop All FK Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 13 个命名混乱的 alembic 迁移清空重建为单个 init_schema 迁移（命名格式 `YYYYMMDD_HHMMSS_<rev>_<slug>.py`），同时删除模型层和数据库层全部外键约束。

**Architecture:**
- 因为 dev server 尚未部署、本地 DB 可随时 drop 重建，方案 α：清空全部旧迁移 + drop DB + 删模型 FK + `alembic revision --autogenerate` 一把生成 init。
- 命名格式靠 `alembic.ini` 的 `file_template` 配置自动产出。
- FK 直接从模型层 `ForeignKey(...)` 调用中删掉，列保留为普通 `BigInteger`，autogenerate 不会生成 FK 约束。

**Tech Stack:** Python 3.12 / SQLAlchemy 2.x / Alembic / PostgreSQL 16 / Docker Compose / pytest

**Spec:** [docs/superpowers/specs/2026-04-27-clean-migrations-and-drop-fk-design.md](../specs/2026-04-27-clean-migrations-and-drop-fk-design.md)

---

## 前置条件

- 当前 git 状态干净（除 `backend/uv.lock` 和 `AlphaPilot Design System/` 目录），spec 已 commit
- 本地 docker 栈可启停（`make local-up` / `make local-down`）
- 假设 `make local-up` 已运行，PostgreSQL 容器在跑（端口 5432）
- backend 虚拟环境已就绪（`backend/.venv`）

---

### Task 1: 清空 alembic 现状 + drop DB

**目标：** 让 `backend/migrations/versions/` 为空、`alembic_version` 表清空、本地 DB schema 清空。

**Files:**
- Delete: `backend/migrations/versions/20260316_0001_init_schema.py`
- Delete: `backend/migrations/versions/20260317_0002_add_system_settings.py`
- Delete: `backend/migrations/versions/20260317_0003_add_users.py`
- Delete: `backend/migrations/versions/20260317_0004_add_admin_tables.py`
- Delete: `backend/migrations/versions/20260421_0001_multi_tenant_accounts.py`
- Delete: `backend/migrations/versions/20260421_0002_factor_schema.py`
- Delete: `backend/migrations/versions/20260421_0003_decision_audit_schema.py`
- Delete: `backend/migrations/versions/20260421_0003a_add_agent_invocations_template_idx.py`
- Delete: `backend/migrations/versions/20260421_0004_insight_schema.py`
- Delete: `backend/migrations/versions/20260421_0004a_add_insight_fk_indexes.py`
- Delete: `backend/migrations/versions/d9076875486b_shadow_ops_schema.py`
- Delete: `backend/migrations/versions/aa150ff7dee5_extend_ai_decisions.py`
- Delete: `backend/migrations/versions/b338184343a4_event_bus_tables.py`
- Delete: `backend/migrations/versions/bbe8a491f942_add_event_outbox_event_id_index.py`

- [ ] **Step 1：确认 docker 栈在跑**

```bash
docker compose -f docker/docker-compose.local.yml ps
```
Expected：`postgres` 容器状态为 `running (healthy)`。如果没起，先 `make local-up`。

- [ ] **Step 2：drop 并重建本地数据库**

```bash
docker compose -f docker/docker-compose.local.yml exec -T postgres psql -U alphapilot -d postgres -c "DROP DATABASE IF EXISTS alphapilot_dev;"
docker compose -f docker/docker-compose.local.yml exec -T postgres psql -U alphapilot -d postgres -c "CREATE DATABASE alphapilot_dev OWNER alphapilot;"
```
Expected：`DROP DATABASE` / `CREATE DATABASE` 成功输出。

- [ ] **Step 3：删除全部旧迁移文件**

```bash
git rm backend/migrations/versions/*.py
```
Expected：14 个文件（13 个真迁移 + 可能的 `__init__.py`）被删除。如果有 `__init__.py`，把它再 add 回来：

```bash
ls backend/migrations/versions/__init__.py 2>/dev/null && git checkout HEAD -- backend/migrations/versions/__init__.py || true
```

- [ ] **Step 4：commit 这一步**

```bash
git commit -m "$(cat <<'EOF'
chore(alembic) 清空旧迁移文件准备重建

- drop 全部 13 个旧迁移文件(命名混乱 + 含外键)
- 同步 drop+create 本地 DB

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: 配置 alembic.ini file_template + 清理 upgrade_db.py

**目标：** 让以后 `alembic revision -m` 默认产出 `YYYYMMDD_HHMMSS_<rev>_<slug>.py`，同时移除 `upgrade_db.py` 里针对旧 init revision id 的 legacy stamp 逻辑（已无意义）。

**Files:**
- Modify: `backend/alembic.ini`（在 `[alembic]` 段加 `file_template` + `truncate_slug_length`）
- Modify: `backend/scripts/upgrade_db.py`（移除 `LEGACY_TABLES` 和 `_needs_legacy_stamp` 兼容逻辑，因为只在升级前的旧 DB 才用得到）

- [ ] **Step 1：编辑 `backend/alembic.ini`**

在 `[alembic]` 段、`script_location = migrations` 之后加两行：

```ini
[alembic]
script_location = migrations
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(rev)s_%%(slug)s
truncate_slug_length = 40
prepend_sys_path = .
path_separator = os
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname
```

注意 `%%`（双百分号）是 ConfigParser 的转义，运行时会变成 `%`。

- [ ] **Step 2：简化 `backend/scripts/upgrade_db.py`**

把整个文件替换为：

```python
"""运行所有待执行的 Alembic 迁移。"""
import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Running pending migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Migrations complete.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3：commit**

```bash
git add backend/alembic.ini backend/scripts/upgrade_db.py
git commit -m "$(cat <<'EOF'
feat(alembic) 配置 file_template 命名格式 + 清理 legacy stamp 逻辑

- 命名格式: YYYYMMDD_HHMMSS_<rev>_<slug>.py
- truncate_slug_length=40
- upgrade_db.py 移除针对 20260316_0001 的 legacy stamp(旧 DB 已不存在)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 删除模型层全部 ForeignKey

**目标：** `backend/src/shared/models/` 下所有 `ForeignKey(...)` 调用清掉，列保留为普通 `BigInteger`。

**Files (21 个，每个文件操作相同)：**
- `backend/src/shared/models/account.py`
- `backend/src/shared/models/account_entity.py`
- `backend/src/shared/models/agent_invocation.py`
- `backend/src/shared/models/attribution.py`
- `backend/src/shared/models/audit_log.py`
- `backend/src/shared/models/candle.py`
- `backend/src/shared/models/decision.py`
- `backend/src/shared/models/decision_review.py`
- `backend/src/shared/models/experience.py`
- `backend/src/shared/models/experience_v2.py`
- `backend/src/shared/models/factor.py`
- `backend/src/shared/models/indicator.py`
- `backend/src/shared/models/order.py`
- `backend/src/shared/models/position.py`
- `backend/src/shared/models/prompt.py`
- `backend/src/shared/models/regime.py`
- `backend/src/shared/models/report.py`
- `backend/src/shared/models/risk_event.py`
- `backend/src/shared/models/shadow.py`
- `backend/src/shared/models/symbol_config.py`
- `backend/src/shared/models/trade.py`

每个文件做两件事：
1. 从 `from sqlalchemy import ...` 中删除 `ForeignKey` 名称（如果该 import 含 `ForeignKey`）
2. 把 `mapped_column(BigInteger, ForeignKey("xxx.id"), <其他参数>)` 改为 `mapped_column(BigInteger, <其他参数>)`

- [ ] **Step 1：写一个临时的批量验证脚本（不入库，仅辅助）**

不需要写脚本，用 grep 验证：

```bash
grep -rn "ForeignKey" backend/src/shared/models/
```
Expected：列出当前 ~30 处 ForeignKey 用法。

- [ ] **Step 2：逐文件改 — `audit_log.py`**

替换：
```python
from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String, Text
```
为：
```python
from sqlalchemy import BigInteger, Integer, JSON, String, Text
```

替换：
```python
account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
```
为：
```python
account_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
```

- [ ] **Step 3：逐文件改 — `candle.py`**

import 行删 `ForeignKey`，把 `account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 4：逐文件改 — `decision_review.py`**

import 行删 `ForeignKey`，把 `decision_id` 列里 `ForeignKey("ai_decisions.id")` 删掉。

- [ ] **Step 5：逐文件改 — `attribution.py`**

import 行删 `ForeignKey`。两列要改：`trade_id`（删 `ForeignKey("trades.id")`）+ `account_id`（删 `ForeignKey("accounts.id")`）。

- [ ] **Step 6：逐文件改 — `trade.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 7：逐文件改 — `decision.py`**

import 行删 `ForeignKey`。三列要改：
- `account_id`：删 `ForeignKey("accounts.id")`
- `proposal_draft_id`：删 `ForeignKey("proposal_drafts.id")`
- `factor_snapshot_id`：删 `ForeignKey("factor_snapshots.id")`

- [ ] **Step 8：逐文件改 — `agent_invocation.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 9：逐文件改 — `position.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 10：逐文件改 — `symbol_config.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 11：逐文件改 — `account_entity.py`**

import 行删 `ForeignKey`。三列要改：
- 第一个 `account_id`（约第 38 行）：删 `ForeignKey("accounts.id")`
- 第二个 `account_id`（约第 59 行）：删 `ForeignKey("accounts.id")`
- `profile_id`（约第 61 行）：删 `ForeignKey("risk_profiles.id")`

- [ ] **Step 12：逐文件改 — `report.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 13：逐文件改 — `order.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 14：逐文件改 — `account.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 15：逐文件改 — `experience.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 16：逐文件改 — `shadow.py`**

import 行删 `ForeignKey`。四列要改：
- `real_decision_id`：删 `ForeignKey("ai_decisions.id")`
- `parameter_version_id`：删 `ForeignKey("parameter_versions.id")`
- `shadow_decision_id`：删 `ForeignKey("shadow_decisions.id")`
- `real_trade_id`：删 `ForeignKey("trades.id")`

- [ ] **Step 17：逐文件改 — `risk_event.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 18：逐文件改 — `prompt.py`**

import 行删 `ForeignKey`。两列要改：
- `account_id`：删 `ForeignKey("accounts.id")`
- `template_id`：删 `ForeignKey("prompt_templates.id")`

- [ ] **Step 19：逐文件改 — `regime.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 20：逐文件改 — `factor.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 21：逐文件改 — `experience_v2.py`**

import 行删 `ForeignKey`。三列要改：
- `account_id`：删 `ForeignKey("accounts.id")`
- `trade_id`：删 `ForeignKey("trades.id")`
- `experience_id`：删 `ForeignKey("experiences.id")`

- [ ] **Step 22：逐文件改 — `indicator.py`**

import 行删 `ForeignKey`，`account_id` 列里 `ForeignKey("accounts.id")` 删掉。

- [ ] **Step 23：验证模型层 0 残留**

```bash
grep -rn "ForeignKey" backend/src/shared/models/
```
Expected：返回 0 行。如果有残留，回去补改。

- [ ] **Step 24：验证 import 是否还能 work**

```bash
cd backend && .venv/Scripts/python -c "from src.shared.models import Base; print(len(Base.metadata.tables))"
```
Expected：打印一个整数（约 30+），不报 ImportError。

- [ ] **Step 25：commit**

```bash
git add backend/src/shared/models/
git commit -m "$(cat <<'EOF'
refactor(models) 删除全部 ForeignKey 约束改为业务层 ID 关联

- 21 个 model 文件共 ~30 处 ForeignKey 调用全部移除
- 关联列保留为普通 BigInteger,nullable/default/index 不变
- 业务层手动维护关联(项目本就没用 relationship)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: autogenerate init 迁移 + review

**目标：** 跑 `alembic revision --autogenerate -m "init_schema"`，得到符合命名规范、不含 FK 的单一 init 迁移。

**Files:**
- Create: `backend/migrations/versions/<auto-generated-filename>.py`（命名形如 `20260427_HHMMSS_<rev>_init_schema.py`）

- [ ] **Step 1：确认环境变量**

确认 `backend/.env`（或者 backend 进程能拿到）的 `DATABASE_URL` 指向本地 `alphapilot_dev`：

```bash
grep DATABASE_URL backend/.env 2>/dev/null || echo "请确认 DATABASE_URL 配置正确"
```

如果用的是 `make` 的本地栈，对应的 env 是 `.env.local`，但 alembic 直接读 `src.shared.config.get_settings()`，会从 `BACKEND_ENV` 决定。一般本地 venv 跑 alembic 会拿到 `.env`。

- [ ] **Step 2：跑 autogenerate**

```bash
cd backend && .venv/Scripts/alembic revision --autogenerate -m "init_schema"
```
Expected：
- 输出形如：`Generating .../20260427_143025_<hash>_init_schema.py ... done`
- 文件名严格遵循 `YYYYMMDD_HHMMSS_<rev>_init_schema.py` 格式
- 文件成功落到 `backend/migrations/versions/`

如果 `.venv` 是 Linux 路径（`bin/`），用 `.venv/bin/alembic`。

- [ ] **Step 3：核对生成的迁移**

打开生成的迁移文件，做以下检查：

1. `grep -i "ForeignKey" backend/migrations/versions/*.py` 必须返回 0 行
2. `grep -c "op.create_table" backend/migrations/versions/*.py` 应大于 25（项目约 30 张表）
3. 文件第一行 docstring 是 `"""init_schema"""`，`Revises: None`

```bash
grep -i "ForeignKey" backend/migrations/versions/*.py
grep -c "op.create_table" backend/migrations/versions/*.py
head -20 backend/migrations/versions/*.py
```

如果有 ForeignKey 残留 → Task 3 漏改了某个 model 文件，回去补，再删此迁移文件重生成。

- [ ] **Step 4：（可选）格式化迁移文件**

```bash
cd backend && .venv/Scripts/ruff format migrations/versions/
```

- [ ] **Step 5：commit**

```bash
git add backend/migrations/versions/
git commit -m "$(cat <<'EOF'
feat(alembic) autogenerate init_schema 单一迁移(无外键)

- 命名格式: YYYYMMDD_HHMMSS_<rev>_init_schema.py
- 30+ 张表一次建完, 不含任何 FK 约束
- 替换原 13 个混乱命名 + 含 FK 的旧迁移

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: 应用迁移到本地 DB + 跑测试

**目标：** 验证 init 迁移能成功 apply，业务层测试不被 FK 删除影响。

- [ ] **Step 1：跑 alembic upgrade**

```bash
cd backend && .venv/Scripts/alembic upgrade head
```
Expected：`INFO ... Running upgrade  -> <hash>, init_schema`，无错误。

- [ ] **Step 2：验证 schema 创建**

```bash
docker compose -f docker/docker-compose.local.yml exec -T postgres psql -U alphapilot -d alphapilot_dev -c "\dt"
```
Expected：列出 30+ 张表。

```bash
docker compose -f docker/docker-compose.local.yml exec -T postgres psql -U alphapilot -d alphapilot_dev -c "SELECT count(*) FROM pg_constraint WHERE contype='f';"
```
Expected：`count = 0`（数据库内 0 条 FK 约束）。

- [ ] **Step 3：跑全部测试**

```bash
make test
```
Expected：53+ tests 全绿。如失败，按以下分类处理：
- ImportError（漏删/漏改）→ 回 Task 3 补
- 表/列缺失 → autogenerate 漏掉了，回 Task 4 修迁移
- FK 行为相关失败（业务依赖了 cascade 删除）→ 业务层修，本计划范围外，记录到 followup

- [ ] **Step 4：跑 lint**

```bash
make lint
```
Expected：无新增错误。

- [ ] **Step 5：commit（如果有任何修补）**

```bash
git add -A && git status
```

如果有 staged 改动，commit：

```bash
git commit -m "$(cat <<'EOF'
fix(alembic) init 迁移落库验证补丁

- <具体修了什么>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

如果没有改动，跳过此 step。

---

### Task 6: 推送 + 部署 dev server

**目标：** 按 CLAUDE.md "自动 push + 自动部署 dev" 规则收口。

- [ ] **Step 1：push 到远程**

```bash
git push
```
Expected：推送 5 个 commit（Task 1-5 各一个，可能 Task 5 没补丁则 4 个）。

- [ ] **Step 2：部署 dev server**

```bash
bash scripts/deploy-dev.sh
```
Expected：dev server 正常启动，`/ap-dev` 可访问。

- [ ] **Step 3：写工程过程日志**

新建 `docs/worklog/20260427_<HHMM>_alembic_clean_drop_fk.md`，记录：
- 做了什么（清空 13 个旧迁移、配置 file_template、删 21 个文件 FK、autogenerate 单一 init）
- 为什么做（命名混乱、不要 DB 层 FK）
- 如何验证（pg_constraint contype='f' = 0、make test 全绿）
- 对应 commit（5 个 commit hash）

```bash
git add docs/worklog/
git commit -m "$(cat <<'EOF'
docs(worklog) Alembic 清理 + FK 移除收口

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

## 验收标准

- [ ] `backend/migrations/versions/` 下只有 1 个迁移文件，命名严格 `YYYYMMDD_HHMMSS_<rev>_init_schema.py`
- [ ] 该文件内 `grep -i ForeignKey` 返回 0 行
- [ ] `backend/src/shared/models/` 下 `grep -rn ForeignKey` 返回 0 行
- [ ] 本地 PostgreSQL `SELECT count(*) FROM pg_constraint WHERE contype='f'` 返回 0
- [ ] `make test` 全绿
- [ ] `make lint` 无新增错误
- [ ] dev server 部署成功，前端能正常加载
- [ ] memory 已记录 alembic 命名规则 + 无 FK 规则（已在 brainstorming 阶段保存到 `feedback_alembic_rules.md`）
