# Stage 2: DB 层扁平化 + 主键统一 + migrations 重建 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 `src/shared/models/` + `src/shared/schemas/` 平铺到 `src/models/` + `src/schemas/`；统一所有主键为纯 `BigInteger autoincrement`（删除 `BigIntPk` sqlite variant + 4 个 Integer 主键升级 BigInteger）；删除现有 `migrations/versions/*` 重新生成；引入 `src/cruds/base_crud.py` + 一实体一 crud；引入 `TradingModeMixin` 按需继承；测试改用真 PostgreSQL。

**Architecture:** model 全局扁平、cruds 全局扁平（B-Hybrid 的 DB 层）；alembic 单初始 migration；测试 fixture 切 testcontainers 起 PG。

**Tech Stack:** SQLAlchemy 2.x / Alembic 1.18+ / PostgreSQL 16 / testcontainers-python

**关联 spec:** v3.7 §3.1, §4.2, §4.3, §6 阶段 2

**前置条件：**
- Stage 1 已合 main（commit `0d2be68`）
- 测试基线：459 passed + 2 skipped 全绿
- dev 数据库可重建（老板明确接受）

**老板的三个决策：**
- 决策 1：删 migrations 重建（C 彻底重构）
- 决策 2：Base **不**收编 id 字段（每个 model 自定义）
- 决策 3：**删 sqlite variant**，所有测试用真 PostgreSQL

---

## File Structure（终态）

```
backend/
├── alembic.ini                            # 保留入口（指向 migrations/）
├── migrations/                            # 重建：仅 1 个初始 migration
│   ├── env.py                             # 调整 target_metadata 指向新 src/models/
│   ├── script.py.mako
│   └── versions/
│       └── <ts>_init_schema_after_v37_refactor.py
└── src/
    ├── models/                            # ⭐ 全局扁平（迁自 src/shared/models/）
    │   ├── __init__.py                    # 显式 import + __all__
    │   ├── base.py                        # Base + TradingModeMixin（不含 id）
    │   ├── enums.py                       # ORM 枚举（迁自 src/shared/enums.py）
    │   ├── account.py
    │   ├── account_entity.py
    │   ├── agent_invocation.py
    │   ├── attribution.py
    │   ├── audit_log.py                   # PK Integer → BigInteger
    │   ├── candle.py
    │   ├── decision.py
    │   ├── decision_review.py
    │   ├── event_store.py
    │   ├── experience.py
    │   ├── experience_v2.py
    │   ├── factor.py
    │   ├── indicator.py
    │   ├── ops_diagnosis.py
    │   ├── order.py
    │   ├── position.py
    │   ├── prompt.py
    │   ├── regime.py
    │   ├── report.py
    │   ├── risk_event.py
    │   ├── shadow.py
    │   ├── symbol_config.py               # PK Integer → BigInteger
    │   ├── system_setting.py              # PK Integer → BigInteger
    │   ├── trade.py
    │   └── user.py                        # PK Integer → BigInteger
    ├── cruds/                             # ⭐ 全新
    │   ├── __init__.py                    # 单例集中导出
    │   ├── base_crud.py                   # BaseCrud[ModelT] + 实体方法命名约定
    │   ├── account_crud.py
    │   ├── audit_log_crud.py
    │   ├── candle_crud.py
    │   ├── decision_crud.py
    │   ├── ...                            # ~26 个
    ├── schemas/                           # ⭐ 全局扁平（迁自 src/shared/schemas/）
    │   ├── __init__.py
    │   ├── pagination.py                  # （或继续用 src/common/schemas/pagination.py）
    │   └── ...                            # 一模块一文件
    └── shared/
        ├── db.py                          # 已 wrapper（不动）
        ├── config.py                      # 已 wrapper（不动）
        ├── enums.py                       # → 阶段 3 处理；本阶段保留 re-export
        ├── models/                        # 改为转发 wrapper（保留兼容）
        ├── schemas/                       # 改为转发 wrapper（保留兼容）
        └── ...
```

---

## 任务清单

### Task 1: 创建 stage2 分支 + 验证基线 + 准备 dev_pg 测试 fixture

**Files:**
- Create: `backend/tests/conftest_pg.py` (postgres fixture)

- [ ] **Step 1: 切到 main + 创建 stage2 分支**

```bash
git checkout main && git pull && git checkout -b refactor/stage2-db-layer
```

- [ ] **Step 2: 验证基线 459 passed**

```bash
cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -q --tb=no
```

Expected: 459 passed + 2 skipped

- [ ] **Step 3: 写基线 worklog**

```bash
WORKLOG="docs/worklog/$(date +%Y%m%d_%H%M)_stage2_baseline.md"
cat > "$WORKLOG" <<EOF
# Stage 2 baseline ($(date '+%Y-%m-%d %H:%M'))
- 起点 commit: $(git rev-parse HEAD)
- pytest: 459 passed + 2 skipped
- 决策：C+不收编+B（彻底重构 + 真 PG 测试）
EOF
git add docs/worklog/
git -c commit.gpgsign=false commit -m "chore(stage2): 记录重构基线"
git push -u origin refactor/stage2-db-layer
```

---

### Task 2: 引入 testcontainers fixture（为后续测试准备真 PG）

**Files:**
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: 在 conftest 增加 module-scoped postgres fixture**

```python
# tests/conftest.py 新增

import pytest


@pytest.fixture(scope="session")
def pg_container_url():
    """Module-scoped real PostgreSQL via testcontainers.
    
    使用真 PG 测试 ORM 行为（Stage 2 后所有 ORM 测试都依赖此 fixture）。
    单测中如不依赖 ORM 可不引用，速度更快。
    """
    from testcontainers.postgres import PostgresContainer
    pg = PostgresContainer("postgres:16-alpine")
    pg.start()
    try:
        yield pg.get_connection_url()
    finally:
        pg.stop()
```

- [ ] **Step 2: 提交**

```bash
git add backend/tests/conftest.py
git -c commit.gpgsign=false commit -m "feat(stage2/task2): tests/conftest.py 增加 pg_container_url session-scoped fixture"
git push
```

---

### Task 3: 创建 src/models/base.py（Base + TradingModeMixin，不含 id）

**Files:**
- Create: `backend/src/models/__init__.py`
- Create: `backend/src/models/base.py`

- [ ] **Step 1: 看现有 src/shared/models/base.py 的字段约定**

```bash
cat backend/src/shared/models/base.py
```

记录：当前 `Base` 类、`BigIntPk`、`TimestampMixin` 的内容。

- [ ] **Step 2: 创建 src/models/base.py**

```python
# backend/src/models/base.py
"""DB Model 基类与公共 Mixin。

约定（v3.7）：
- Base 不含 id 字段（每个 model 自定义 BigInteger autoincrement）
- TradingModeMixin 按需继承（要做交易环境隔离的表才继承）
- 不再使用 BigIntPk 类型别名（删 sqlite variant，统一用 BigInteger）
- TimestampMixin 提供 created_at / updated_at
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM model 的基类。

    显式约定：
    - 不在此基类提供 id（避免遮蔽各 model 自定义类型 / 列名）
    - 通用字段通过 Mixin 显式继承
    """


class TradingModeMixin:
    """需要按 testnet/mainnet 隔离的表显式继承。"""
    trading_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="testnet/mainnet 数据隔离"
    )


class TimestampMixin:
    """所有需要时间戳的表继承。"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """需要软删除的表继承（可选）。"""
    enable_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("TRUE")
    )
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE")
    )
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/models/
git -c commit.gpgsign=false commit -m "feat(stage2/task3): src/models/base.py — Base + 三个 Mixin（无 id 字段）"
git push
```

---

### Task 4-N（合批处理）: 把 26 个 model 从 src/shared/models/ 迁到 src/models/，统一主键 BigInteger

由于工作量大且批量同质，按以下规则一次性处理（**不是 26 个独立 task**）：

**对每个 model 文件**：

1. 复制 `src/shared/models/<name>.py` 到 `src/models/<name>.py`
2. 修改 import：
   - `from src.shared.models.base import Base, BigIntPk, TimestampMixin` →
     `from src.models.base import Base, TimestampMixin`（如需 trading_mode 加 `, TradingModeMixin`）
3. 修改主键类型：`BigIntPk` → `BigInteger`（直接 from sqlalchemy import BigInteger）
4. 4 个特殊 model 主键升级 Integer → BigInteger：
   - `audit_log.py` / `symbol_config.py` / `system_setting.py` / `user.py`
5. 跨表 ID 列：`Mapped[int] = mapped_column(Integer, ...)` → `mapped_column(BigInteger, ...)` 检查所有 `_id` 后缀字段
6. 添加 `TradingModeMixin` 继承（参照 spec §4.2.3 表）：
   - **需要 trading_mode**：account / candle / decision / experience / factor / indicator / order / position / regime / report / risk_event / trade / 等业务表
   - **不需要**：user / system_setting / audit_log / symbol_config / agent_invocation 等

**批量执行步骤：**

- [ ] **Step 1: 在 src/models/ 创建 __init__.py 显式 import 全部**

```python
# src/models/__init__.py
"""ORM models 集中导出（alembic 自动 metadata 收集 + IDE 跳转友好）。"""
from src.models.base import Base, SoftDeleteMixin, TimestampMixin, TradingModeMixin
from src.models.account import Account
from src.models.account_entity import AccountEntity
# ... 26 个 model 全部显式导入

__all__ = [
    "Base", "SoftDeleteMixin", "TimestampMixin", "TradingModeMixin",
    "Account", "AccountEntity",
    # ... 完整列表
]
```

- [ ] **Step 2: 编写迁移脚本（一次性 Python 脚本生成 26 个 model）**

```bash
# scripts/migrate_models_to_v37.py（迁完即删）
# - 读取 src/shared/models/<name>.py
# - sed 替换 BigIntPk → BigInteger
# - 添加 from sqlalchemy import BigInteger
# - 检测是否需要 TradingModeMixin（按白名单）
# - 写到 src/models/<name>.py
```

- [ ] **Step 3: 改 src/shared/models/ 为转发 wrapper**

```python
# src/shared/models/__init__.py
"""向后兼容 — 阶段 3 全面迁移完成后删除。"""
from src.models import *  # noqa: F401, F403
from src.models import __all__  # noqa: F401
```

- [ ] **Step 4: 删除 BigIntPk 别名**

`src/shared/models/base.py` 删除 `BigIntPk` 定义；所有引用必须用 `BigInteger`。

- [ ] **Step 5: 跑测试（依赖 PG fixture）**

```bash
cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -q tests/unit/test_models.py -v
```

如果 sqlite in-memory 测试失败，**改用 testcontainers PG**。

- [ ] **Step 6: 提交**

```bash
git add backend/src/models/ backend/src/shared/models/
git -c commit.gpgsign=false commit -m "refactor(stage2/task4): 26 个 model 迁到 src/models/，统一 BigInteger 主键"
git push
```

---

### Task 5: 创建 src/cruds/base_crud.py + BaseCrud[ModelT]

**Files:**
- Create: `backend/src/cruds/__init__.py`
- Create: `backend/src/cruds/base_crud.py`
- Test: `backend/tests/unit/cruds/test_base_crud.py`

- [ ] **Step 1: 实现 BaseCrud**

```python
# src/cruds/base_crud.py
"""BaseCrud[ModelT] — 提供 95% 标准 CRUD 操作。

子类只需 ``model = SomeModel``，extra 方法按 spec §4.3 命名约定（mark_xxx /
find_xxx / bulk_mark_xxx / bump_xxx / update_progress）。
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.exception.errors import DBException
from src.common.response.response_code import ErrorCode
from src.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseCrud(Generic[ModelT]):
    """所有实体 crud 的基类。"""

    model: type[ModelT]

    def add(self, session: Session, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        session.add(obj)
        session.flush()
        return obj

    def get(self, session: Session, id: int) -> ModelT:
        obj = session.get(self.model, id)
        if obj is None:
            raise DBException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"{self.model.__name__} id={id} not found",
            )
        return obj

    def get_or_none(self, session: Session, id: int) -> ModelT | None:
        return session.get(self.model, id)

    def find_by_status(self, session: Session, statuses: list[str]) -> list[ModelT]:
        if not hasattr(self.model, "status"):
            raise NotImplementedError(f"{self.model.__name__} has no 'status' column")
        return list(
            session.execute(
                select(self.model).where(self.model.status.in_(statuses))
            ).scalars()
        )

    def update(self, session: Session, id: int, **kwargs: Any) -> ModelT:
        obj = self.get(session, id)
        for k, v in kwargs.items():
            setattr(obj, k, v)
        session.flush()
        return obj

    def delete(self, session: Session, id: int) -> None:
        """软删（要求 model 有 delete_flag 字段）。"""
        obj = self.get(session, id)
        if hasattr(obj, "delete_flag"):
            obj.delete_flag = True
            session.flush()
        else:
            session.delete(obj)
            session.flush()

    def hard_delete(self, session: Session, id: int) -> None:
        obj = self.get(session, id)
        session.delete(obj)
        session.flush()
```

- [ ] **Step 2: 测试（用真 PG fixture）**

```python
# tests/unit/cruds/test_base_crud.py
# 用 pg_container_url fixture 创建 engine，验证 BaseCrud 行为
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/cruds/ backend/tests/unit/cruds/
git -c commit.gpgsign=false commit -m "feat(stage2/task5): src/cruds/base_crud.py — BaseCrud[ModelT]"
git push
```

---

### Task 6: 26 个实体 crud（一实体一文件）

按 BaseCrud 模式批量生成：

```python
# src/cruds/<entity>_crud.py
from src.cruds.base_crud import BaseCrud
from src.models.<entity> import <Entity>


class <Entity>Crud(BaseCrud[<Entity>]):
    model = <Entity>

    # 实体专属方法（按需）：
    # def find_by_xxx(...): ...
    # def mark_xxx(...): ...


<entity>_crud = <Entity>Crud()
```

- [ ] **Step 1: 写 Python 脚本批量生成 26 个 stub**
- [ ] **Step 2: 在 src/cruds/__init__.py 集中暴露所有 crud 单例**
- [ ] **Step 3: 提交**

---

### Task 7: 删 migrations/versions 重建

- [ ] **Step 1: 备份现有 migrations 到 docs/worklog/**

```bash
cp -r backend/migrations/versions /tmp/migrations_backup_$(date +%s)/
```

- [ ] **Step 2: 删除 migrations/versions/*.py**

```bash
find backend/migrations/versions -name '*.py' ! -name '__init__.py' -delete
```

- [ ] **Step 3: 调整 alembic env.py 指向新 src/models/**

- [ ] **Step 4: 重新 autogenerate**

```bash
cd backend && uv run alembic revision --autogenerate -m "init_schema_after_v37_refactor"
```

- [ ] **Step 5: 人工 review 新 migration**：所有表主键 BIGINT IDENTITY，跨表关联列 BIGINT

- [ ] **Step 6: 干净 dev 库测试**

```bash
docker exec -it alpha-pilot_postgres dropdb -U alphapilot alphapilot
docker exec -it alpha-pilot_postgres createdb -U alphapilot alphapilot
cd backend && uv run alembic upgrade head
```

- [ ] **Step 7: 提交**

---

### Task 8: schemas 路径搬迁 src/shared/schemas/ → src/schemas/

类似 Task 4，批量搬迁 + 转发兼容 + 跑测试。

---

### Task 9: 业务代码切到 cruds（service 层不再裸 SQL）

- [ ] **Step 1: grep `session.query(Model)` 全文，替换为 `<entity>_crud.find_xxx()`**
- [ ] **Step 2: 跑全量测试**
- [ ] **Step 3: 提交**

---

### Task 10: Stage 2 完成 worklog + dev 部署 + 24h 观察

- [ ] **Step 1: 跑全量测试 459+ passed**
- [ ] **Step 2: dev 重建 + alembic upgrade**
- [ ] **Step 3: dev 验证业务接口（持仓/决策/平仓）行为不变**
- [ ] **Step 4: 写 Stage 2 完成 worklog**
- [ ] **Step 5: PR 合 main**

---

## Stage 2 验收清单

- [ ] 全量测试 ≥ 459 passed（不允许下降）
- [ ] 干净 PG 库 `alembic upgrade head` 单 migration 跑通
- [ ] 所有表主键 `BIGINT IDENTITY`（user/audit_log/symbol_config/system_setting 也升级）
- [ ] `grep -r "BigIntPk" src/` 无结果
- [ ] `grep -r "from src.shared.models" src/ tests/ --include='*.py'` 全部走兼容 wrapper（不动业务）
- [ ] 业务行为零变化（持仓 / 决策 / 平仓 / WebSocket 推送）
- [ ] dev 重建后正常运行 24h
- [ ] worklog 写入 docs/worklog/

---

## Stage 2 完成后 → Stage 3

调用 writing-plans 展开 Stage 3 plan：业务层重组（services/{execution,insight,strategy,risk}/ + core/）。
