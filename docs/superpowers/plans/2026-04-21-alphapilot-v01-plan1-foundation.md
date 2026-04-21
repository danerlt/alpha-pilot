# AlphaPilot V0.1 Plan 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation layer for AlphaPilot V1.0 target architecture — complete V1.0 database schema (multi-tenant prep), event bus (Redis Streams + Outbox/Inbox with in-process fast path), and Binance exchange adapter with RateLimiter + retry. No business logic yet; this plan only produces the primitives later plans will build on.

**Architecture:** Four-plane separation with events as the only inter-plane contract (per spec §2.1). This plan implements the **shared primitives** (schema, event bus, exchange adapter) that all four planes depend on. `account_id` is added everywhere from day one so multi-tenancy is a schema-level constant, not a future migration.

**Tech Stack:** Python 3.12, SQLAlchemy 2.x, Alembic, FastAPI, Pydantic v2, Redis 7 Streams, pytest + testcontainers (Postgres + Redis), python-binance.

**Spec reference:** `docs/superpowers/specs/2026-04-21-alphapilot-v1-system-design.md` §2, §3, §5, §6.

---

## File Structure

### Created in this plan

```
backend/
├─ migrations/versions/
│  ├─ 20260421_0001_multi_tenant_accounts.py        # Task 1
│  ├─ 20260421_0002_factor_schema.py                # Task 2
│  ├─ 20260421_0003_decision_audit_schema.py        # Task 3
│  ├─ 20260421_0004_insight_schema.py               # Task 4
│  ├─ 20260421_0005_shadow_ops_schema.py            # Task 5
│  ├─ 20260421_0006_extend_ai_decisions.py          # Task 6
│  └─ 20260421_0007_event_bus_tables.py             # Task 10
├─ src/
│  ├─ shared/models/
│  │  ├─ account_entity.py        # Task 1 (accounts, risk_profiles, parameter_versions)
│  │  ├─ factor.py                # Task 2 (factor_definitions, factor_snapshots, factor_candidates)
│  │  ├─ prompt.py                # Task 3 (prompt_templates, proposal_drafts)
│  │  ├─ decision_review.py       # Task 3 (decision_reviews)
│  │  ├─ agent_invocation.py      # Task 3 (agent_invocations)
│  │  ├─ experience_v2.py         # Task 4 (experiences, experience_summaries)
│  │  ├─ attribution.py           # Task 4 (trade_attributions, strategy_scores)
│  │  ├─ shadow.py                # Task 5 (shadow_decisions, shadow_evaluations)
│  │  ├─ ops_diagnosis.py         # Task 5 (ops_diagnoses)
│  │  └─ event_store.py           # Task 10 (event_inbox, event_outbox)
│  ├─ events/
│  │  ├─ __init__.py              # Task 8
│  │  ├─ ids.py                   # Task 7 (UUIDv7 utility)
│  │  ├─ contracts.py             # Task 8 (all event dataclasses)
│  │  ├─ bus.py                   # Task 11 (EventBus abstract + adapters)
│  │  ├─ outbox.py                # Task 12 (Outbox writer + shuttle worker)
│  │  └─ inbox.py                 # Task 13 (Inbox idempotency helper)
│  ├─ execution/
│  │  ├─ __init__.py              # Task 14
│  │  └─ exchange/
│  │     ├─ __init__.py           # Task 14
│  │     ├─ types.py              # Task 14 (Kline, Ticker, OrderRequest, OrderResult)
│  │     ├─ adapter.py            # Task 14 (abstract base)
│  │     ├─ rate_limiter.py       # Task 15 (token bucket)
│  │     ├─ retry.py              # Task 16 (exponential backoff)
│  │     └─ binance_adapter.py    # Task 17 (Binance implementation)
│  └─ workers/
│     └─ event_shuttle.py         # Task 12 (Outbox → Redis Streams worker)
└─ tests/
   ├─ unit/
   │  ├─ models/
   │  │  ├─ test_multi_tenant_models.py    # Task 1
   │  │  ├─ test_factor_models.py          # Task 2
   │  │  ├─ test_decision_audit_models.py  # Task 3
   │  │  ├─ test_insight_models.py         # Task 4
   │  │  └─ test_shadow_ops_models.py      # Task 5
   │  ├─ events/
   │  │  ├─ test_ids.py                    # Task 7
   │  │  ├─ test_contracts.py              # Task 8
   │  │  ├─ test_outbox.py                 # Task 12
   │  │  └─ test_inbox.py                  # Task 13
   │  └─ execution/
   │     ├─ test_rate_limiter.py           # Task 15
   │     └─ test_retry.py                  # Task 16
   └─ integration/
      ├─ test_schema_account_id.py         # Task 1 (verifies account_id on all tables)
      ├─ test_event_bus_streams.py         # Task 11 (Redis Streams pub/consume/ack)
      ├─ test_event_shuttle.py             # Task 12 (Outbox → Streams end-to-end)
      └─ test_binance_adapter.py           # Task 17 (Binance testnet live call)
```

### Modified in this plan

```
backend/src/shared/models/
  ├─ __init__.py                          # every task (new model exports)
  ├─ position.py                          # Task 1 (add account_id)
  ├─ order.py                             # Task 1
  ├─ trade.py                             # Task 1
  ├─ candle.py                            # Task 1
  ├─ indicator.py                         # Task 1
  ├─ regime.py                            # Task 1
  ├─ account.py                           # Task 1 (AccountSnapshot: add account_id)
  ├─ decision.py                          # Task 1 + Task 6 (account_id + new columns)
  ├─ experience.py                        # Task 1 (old ExperienceRecord; adds account_id)
  ├─ risk_event.py                        # Task 1
  ├─ symbol_config.py                     # Task 1
  ├─ audit_log.py                         # Task 1
  └─ report.py                            # Task 1 (DailyReport)

backend/pyproject.toml                    # Task 7 (add uuid6 lib), Task 11 (fakeredis for tests)
```

---

## Conventions Used Throughout

- **Migrations** are named `YYYYMMDD_NNNN_<description>.py`, `down_revision` always chains to the previous migration. The init migration is `20260316_0001_init_schema`; this plan starts at `20260421_0001`.
- **New tables** always include: `id BigInteger PK autoincrement`, `account_id BigInteger nullable=False default=1`, `created_at/updated_at` via `TimestampMixin`, FKs declared explicitly where cross-referenced.
- **Models** use SQLAlchemy 2.x `Mapped[...]` + `mapped_column`. `Base` and `TimestampMixin` come from `src.shared.models.base`.
- **Tests** use pytest; integration tests use `testcontainers[postgres,redis]` (already in dev deps per `pyproject.toml`).
- **Run tests** with `cd backend && .venv/bin/pytest -q <path>` (the project uses a venv; if missing, `uv sync --extra dev` or `pip install -e '.[dev]'` first).
- **Every task ends with**: run tests → git add → git commit → git push (per `CLAUDE.md` auto-push rule). For brevity, the push command is shown once in Task 1 and implied thereafter.
- **Commit message prefix**: `foundation(plan1):` for all commits in this plan.

---

## Task 1: Multi-tenant Schema Foundation (accounts + account_id on existing + risk_profiles + parameter_versions)

**Goal:** Add `accounts`, `risk_profiles`, `parameter_versions` tables, and retrofit `account_id` FK onto all existing business tables with default value `1` (the single bootstrap account).

**Files:**
- Create: `backend/migrations/versions/20260421_0001_multi_tenant_accounts.py`
- Create: `backend/src/shared/models/account_entity.py`
- Modify: `backend/src/shared/models/__init__.py`
- Modify: `backend/src/shared/models/{position,order,trade,candle,indicator,regime,account,decision,experience,risk_event,symbol_config,audit_log,report}.py` (add `account_id` column)
- Create test: `backend/tests/integration/test_schema_account_id.py`
- Create test: `backend/tests/unit/models/test_multi_tenant_models.py`

### Steps

- [ ] **Step 1.1: Write failing integration test for `account_id` on every existing business table**

Create `backend/tests/integration/test_schema_account_id.py`:

```python
"""Verifies that all business tables have account_id column after migration 0001.

Uses SQLAlchemy's inspector to introspect the live schema.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config

REQUIRED_TABLES = [
    "accounts",
    "risk_profiles",
    "parameter_versions",
    "positions",
    "orders",
    "trades",
    "candles",
    "indicator_snapshots",
    "regime_snapshots",
    "account_snapshots",
    "ai_decisions",
    "risk_events",
    "experience_store",
    "daily_reports",
    "symbol_configs",
    "audit_logs",
]


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        engine = create_engine(url)
        cfg = Config(os.path.join(os.path.dirname(__file__), "../../alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")
        yield engine


def test_all_business_tables_have_account_id(pg_engine):
    inspector = inspect(pg_engine)
    existing = set(inspector.get_table_names())
    missing = [t for t in REQUIRED_TABLES if t not in existing]
    assert not missing, f"missing tables after migration: {missing}"

    tables_that_need_account_id = [t for t in REQUIRED_TABLES if t != "accounts"]
    for table in tables_that_need_account_id:
        cols = {c["name"] for c in inspector.get_columns(table)}
        assert "account_id" in cols, f"{table} missing account_id column"


def test_default_account_row_exists(pg_engine):
    from sqlalchemy import text
    with pg_engine.connect() as conn:
        row = conn.execute(text("SELECT id, owner_user_id, name, enabled FROM accounts WHERE id = 1")).first()
        assert row is not None, "default account (id=1) not bootstrapped"
        assert row.enabled is True
```

- [ ] **Step 1.2: Run the test to confirm it fails**

Run: `cd backend && .venv/bin/pytest -q tests/integration/test_schema_account_id.py -v`
Expected: FAIL — missing `accounts`, `risk_profiles`, `parameter_versions` tables; existing tables missing `account_id` column.

- [ ] **Step 1.3: Write the migration `20260421_0001_multi_tenant_accounts.py`**

Create `backend/migrations/versions/20260421_0001_multi_tenant_accounts.py`:

```python
"""multi-tenant foundation: accounts, risk_profiles, parameter_versions, account_id FKs

Revision ID: 20260421_0001
Revises: 20260317_0004
Create Date: 2026-04-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0001"
down_revision: Union[str, Sequence[str], None] = "20260317_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")

# Existing business tables that get account_id retrofitted. All backfill with account_id=1.
EXISTING_TABLES_NEEDING_ACCOUNT_ID = [
    "positions",
    "orders",
    "trades",
    "candles",
    "indicator_snapshots",
    "regime_snapshots",
    "account_snapshots",
    "ai_decisions",
    "risk_events",
    "experience_store",
    "daily_reports",
    "symbol_configs",
    "audit_logs",
]


def upgrade() -> None:
    # 1. accounts — single-tenant default + multi-tenant prep
    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("exchange", sa.String(length=20), nullable=False, server_default="binance"),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("api_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("risk_profile_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    # 2. risk_profiles — hard limits (learnable=false) + soft (learnable=true)
    op.create_table(
        "risk_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(length=80), nullable=False),
        # HARD (learnable=false)
        sa.Column("max_position_size_pct", sa.Numeric(5, 4), nullable=False, server_default="0.20"),
        sa.Column("max_daily_loss_pct", sa.Numeric(5, 4), nullable=False, server_default="0.03"),
        sa.Column("max_consecutive_losses", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("max_single_risk_pct", sa.Numeric(5, 4), nullable=False, server_default="0.01"),
        # SOFT (learnable=true)
        sa.Column("min_rr_ratio", sa.Numeric(5, 2), nullable=False, server_default="1.5"),
        sa.Column("sl_atr_min_mult", sa.Numeric(5, 2), nullable=False, server_default="0.5"),
        sa.Column("sl_atr_max_mult", sa.Numeric(5, 2), nullable=False, server_default="5.0"),
        sa.Column("regime_thresholds_json", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_risk_profiles_account"),
    )

    # 3. parameter_versions — learning controller audit (empty in V0.1)
    op.create_table(
        "parameter_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("profile_id", sa.BigInteger(), nullable=True),
        sa.Column("change_type", sa.String(length=40), nullable=False),
        sa.Column("old_value_json", sa.JSON(), nullable=True),
        sa.Column("new_value_json", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("proposed_by_agent", sa.String(length=40), nullable=True),
        sa.Column("validated_by", sa.String(length=40), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_parameter_versions_account"),
        sa.ForeignKeyConstraint(["profile_id"], ["risk_profiles.id"], name="fk_parameter_versions_profile"),
    )

    # 4. Bootstrap default account (id=1) + default risk profile
    op.execute(
        "INSERT INTO accounts (id, name, exchange, trading_mode, enabled) "
        "VALUES (1, 'default', 'binance', 'testnet', TRUE) "
        "ON CONFLICT (id) DO NOTHING"
    )
    op.execute(
        "INSERT INTO risk_profiles (id, account_id, name, active) "
        "VALUES (1, 1, 'default', TRUE) "
        "ON CONFLICT (id) DO NOTHING"
    )
    op.execute("UPDATE accounts SET risk_profile_id = 1 WHERE id = 1")

    # 5. Retrofit account_id onto every existing business table + backfill + index
    for table in EXISTING_TABLES_NEEDING_ACCOUNT_ID:
        op.add_column(
            table,
            sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        )
        op.create_foreign_key(
            f"fk_{table}_account", table, "accounts", ["account_id"], ["id"]
        )
        op.create_index(f"ix_{table}_account_id", table, ["account_id"])


def downgrade() -> None:
    for table in EXISTING_TABLES_NEEDING_ACCOUNT_ID:
        op.drop_index(f"ix_{table}_account_id", table_name=table)
        op.drop_constraint(f"fk_{table}_account", table, type_="foreignkey")
        op.drop_column(table, "account_id")
    op.drop_table("parameter_versions")
    op.drop_table("risk_profiles")
    op.drop_table("accounts")
```

Verify migration head chain:

```bash
cd backend && .venv/bin/alembic history
```

The last entry should show `20260317_0004 → 20260421_0001`.

- [ ] **Step 1.4: Create the three new model files and update `__init__.py`**

Create `backend/src/shared/models/account_entity.py`:

```python
"""Multi-tenant entities: Account, RiskProfile, ParameterVersion.

Named account_entity.py (not account.py) to avoid clashing with the existing
AccountSnapshot model in account.py.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, default="binance")
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    api_key_encrypted: Mapped[str | None] = mapped_column(Text)
    api_secret_encrypted: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    risk_profile_id: Mapped[int | None] = mapped_column(BigInteger)


class RiskProfile(Base, TimestampMixin):
    __tablename__ = "risk_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    # HARD — learnable=false
    max_position_size_pct: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.20)
    max_daily_loss_pct: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.03)
    max_consecutive_losses: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_single_risk_pct: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.01)
    # SOFT — learnable=true
    min_rr_ratio: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.5)
    sl_atr_min_mult: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.5)
    sl_atr_max_mult: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=5.0)
    regime_thresholds_json: Mapped[dict | None] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ParameterVersion(Base, TimestampMixin):
    __tablename__ = "parameter_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    profile_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("risk_profiles.id"))
    change_type: Mapped[str] = mapped_column(String(40), nullable=False)
    old_value_json: Mapped[dict | None] = mapped_column(JSON)
    new_value_json: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    proposed_by_agent: Mapped[str | None] = mapped_column(String(40))
    validated_by: Mapped[str | None] = mapped_column(String(40))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

Update `backend/src/shared/models/__init__.py` — add imports and `__all__` entries:

```python
from src.shared.models.account_entity import Account, RiskProfile, ParameterVersion
```

Add `"Account", "RiskProfile", "ParameterVersion"` to `__all__`.

- [ ] **Step 1.5: Add `account_id` to every existing business model**

Apply the identical pattern to 13 model files: (1) add `ForeignKey` to the
`sqlalchemy` import line if not already imported; (2) insert one new
`account_id` `mapped_column` line immediately after the `trading_mode`
column (or after `id` if the model has no `trading_mode`).

Concrete example — `backend/src/shared/models/position.py`:

```python
# BEFORE
from sqlalchemy import String, Numeric, DateTime, BigInteger
...
class Position(Base, TimestampMixin):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    ...

# AFTER
from sqlalchemy import String, Numeric, DateTime, BigInteger, ForeignKey
...
class Position(Base, TimestampMixin):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default=TradingMode.TESTNET.value)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    ...
```

Apply the same pattern to the remaining 12 files (all contain a `trading_mode`
column, so insertion point is consistent):

1. `position.py` (example above)
2. `order.py`
3. `trade.py`
4. `candle.py`
5. `indicator.py` (IndicatorSnapshot)
6. `regime.py` (RegimeSnapshot)
7. `account.py` (AccountSnapshot)
8. `decision.py` (AIDecision)
9. `experience.py` (ExperienceRecord)
10. `risk_event.py` (RiskEvent)
11. `symbol_config.py` (SymbolConfig — insert after `id` since no `trading_mode`)
12. `audit_log.py` (AuditLog — insert after `id`)
13. `report.py` (DailyReport)

Note: `symbol_config.py` and `audit_log.py` don't have `trading_mode`; insert
`account_id` right after `id` instead.

- [ ] **Step 1.6: Write a unit test that instantiating each modified model with default `account_id=1` works**

Create `backend/tests/unit/models/test_multi_tenant_models.py`:

```python
"""Verifies that all retrofitted models expose account_id with default=1."""
from __future__ import annotations

from src.shared.models import (
    Account, AccountSnapshot, AIDecision, AuditLog, Candle, DailyReport,
    ExperienceRecord, IndicatorSnapshot, Order, ParameterVersion, Position,
    RegimeSnapshot, RiskEvent, RiskProfile, SymbolConfig, Trade,
)

MULTI_TENANT_MODELS = [
    Position, Order, Trade, Candle, IndicatorSnapshot, RegimeSnapshot,
    AccountSnapshot, AIDecision, ExperienceRecord, RiskEvent, SymbolConfig,
    AuditLog, DailyReport, RiskProfile, ParameterVersion,
]


def test_every_business_model_has_account_id_column():
    for model in MULTI_TENANT_MODELS:
        assert "account_id" in model.__table__.columns, f"{model.__name__} missing account_id"


def test_account_id_default_is_one():
    for model in MULTI_TENANT_MODELS:
        col = model.__table__.columns["account_id"]
        assert col.default.arg == 1 or str(col.default.arg) == "1", f"{model.__name__}.account_id default != 1"


def test_account_model_has_no_account_id():
    assert "account_id" not in Account.__table__.columns, "Account must not self-reference"
```

- [ ] **Step 1.7: Run all tests**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_multi_tenant_models.py tests/integration/test_schema_account_id.py
```

Expected: PASS both. If the integration test is slow due to container startup, add `@pytest.mark.slow` marker and run separately.

- [ ] **Step 1.8: Commit + push**

```bash
cd E:/ai/alpha-pilot
git add backend/migrations/versions/20260421_0001_multi_tenant_accounts.py \
        backend/src/shared/models/account_entity.py \
        backend/src/shared/models/__init__.py \
        backend/src/shared/models/position.py \
        backend/src/shared/models/order.py \
        backend/src/shared/models/trade.py \
        backend/src/shared/models/candle.py \
        backend/src/shared/models/indicator.py \
        backend/src/shared/models/regime.py \
        backend/src/shared/models/account.py \
        backend/src/shared/models/decision.py \
        backend/src/shared/models/experience.py \
        backend/src/shared/models/risk_event.py \
        backend/src/shared/models/symbol_config.py \
        backend/src/shared/models/audit_log.py \
        backend/src/shared/models/report.py \
        backend/tests/unit/models/test_multi_tenant_models.py \
        backend/tests/integration/test_schema_account_id.py

git commit -m "$(cat <<'EOF'
foundation(plan1): add multi-tenant schema (accounts, risk_profiles, parameter_versions) + account_id on all business tables

Bootstraps default account id=1 and default risk_profile id=1. All V0.1
code continues to run against account_id=1 implicitly; future multi-
tenant work flips the constant.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

git push origin main
```

---

## Task 2: Factor Layer Schema (factor_definitions + factor_snapshots + factor_candidates)

**Goal:** Create the factor-layer persistence for spec §5.2. `factor_definitions` stores versioned factor definitions; `factor_snapshots` stores per-candle factor values (one row per `account_id × symbol × timeframe × open_time`); `factor_candidates` is an empty V0.3+ placeholder.

**Files:**
- Create: `backend/migrations/versions/20260421_0002_factor_schema.py`
- Create: `backend/src/shared/models/factor.py`
- Modify: `backend/src/shared/models/__init__.py`
- Create test: `backend/tests/unit/models/test_factor_models.py`

### Steps

- [ ] **Step 2.1: Write the failing model test**

Create `backend/tests/unit/models/test_factor_models.py`:

```python
from __future__ import annotations

from src.shared.models import FactorCandidate, FactorDefinition, FactorSnapshot


def test_factor_definition_has_core_columns():
    cols = set(FactorDefinition.__table__.columns.keys())
    assert {"id", "name", "version", "inputs_json", "description", "formula_code_ref", "active"} <= cols


def test_factor_snapshot_unique_key():
    cols = FactorSnapshot.__table__.columns
    assert "account_id" in cols
    assert "symbol" in cols
    assert "timeframe" in cols
    assert "open_time" in cols
    assert "factors_json" in cols


def test_factor_snapshot_account_id_default():
    col = FactorSnapshot.__table__.columns["account_id"]
    assert col.default.arg == 1 or str(col.default.arg) == "1"


def test_factor_candidate_exists_for_v03():
    cols = set(FactorCandidate.__table__.columns.keys())
    assert {"id", "proposed_by_agent", "name", "validation_status"} <= cols
```

- [ ] **Step 2.2: Run the test and verify it fails**

Run: `cd backend && .venv/bin/pytest -q tests/unit/models/test_factor_models.py`
Expected: `ImportError: cannot import name 'FactorDefinition'` etc.

- [ ] **Step 2.3: Write the migration**

Create `backend/migrations/versions/20260421_0002_factor_schema.py`:

```python
"""factor layer schema: factor_definitions, factor_snapshots, factor_candidates

Revision ID: 20260421_0002
Revises: 20260421_0001
Create Date: 2026-04-21 00:00:01.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0002"
down_revision: Union[str, Sequence[str], None] = "20260421_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "factor_definitions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("inputs_json", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("formula_code_ref", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    op.create_index("ix_factor_definitions_name_version", "factor_definitions", ["name", "version"], unique=True)

    op.create_table(
        "factor_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("factors_json", sa.JSON(), nullable=False),
        sa.Column("factor_def_versions_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_factor_snapshots_account"),
    )
    op.create_index(
        "ix_factor_snapshots_unique",
        "factor_snapshots",
        ["account_id", "trading_mode", "symbol", "timeframe", "open_time"],
        unique=True,
    )

    op.create_table(
        "factor_candidates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("proposed_by_agent", sa.String(length=40), nullable=False, server_default="factor_ai"),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("formula_code_ref", sa.String(length=200), nullable=True),
        sa.Column("validation_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("validation_report_json", sa.JSON(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )


def downgrade() -> None:
    op.drop_table("factor_candidates")
    op.drop_index("ix_factor_snapshots_unique", table_name="factor_snapshots")
    op.drop_table("factor_snapshots")
    op.drop_index("ix_factor_definitions_name_version", table_name="factor_definitions")
    op.drop_table("factor_definitions")
```

- [ ] **Step 2.4: Write the model file**

Create `backend/src/shared/models/factor.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class FactorDefinition(Base, TimestampMixin):
    __tablename__ = "factor_definitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    inputs_json: Mapped[dict | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    formula_code_ref: Mapped[str | None] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FactorSnapshot(Base, TimestampMixin):
    __tablename__ = "factor_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    factors_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    factor_def_versions_json: Mapped[dict | None] = mapped_column(JSON)


class FactorCandidate(Base, TimestampMixin):
    __tablename__ = "factor_candidates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proposed_by_agent: Mapped[str] = mapped_column(String(40), nullable=False, default="factor_ai")
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    formula_code_ref: Mapped[str | None] = mapped_column(String(200))
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    validation_report_json: Mapped[dict | None] = mapped_column(JSON)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

Update `backend/src/shared/models/__init__.py`:

```python
from src.shared.models.factor import FactorDefinition, FactorSnapshot, FactorCandidate
```

Add `"FactorDefinition", "FactorSnapshot", "FactorCandidate"` to `__all__`.

- [ ] **Step 2.5: Run tests to confirm PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_factor_models.py
```

Expected: PASS.

- [ ] **Step 2.6: Commit + push**

```bash
git add backend/migrations/versions/20260421_0002_factor_schema.py \
        backend/src/shared/models/factor.py \
        backend/src/shared/models/__init__.py \
        backend/tests/unit/models/test_factor_models.py
git commit -m "foundation(plan1): add factor layer schema (definitions, snapshots, candidates)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 3: Decision Audit Schema (prompt_templates + proposal_drafts + decision_reviews + agent_invocations)

**Goal:** Create tables that support multi-agent decomposition and full decision auditability per spec §4.6 and §6.6.

**Files:**
- Create: `backend/migrations/versions/20260421_0003_decision_audit_schema.py`
- Create: `backend/src/shared/models/prompt.py`
- Create: `backend/src/shared/models/decision_review.py`
- Create: `backend/src/shared/models/agent_invocation.py`
- Modify: `backend/src/shared/models/__init__.py`
- Create test: `backend/tests/unit/models/test_decision_audit_models.py`

### Steps

- [ ] **Step 3.1: Write the failing model test**

Create `backend/tests/unit/models/test_decision_audit_models.py`:

```python
from __future__ import annotations

from src.shared.models import AgentInvocation, DecisionReview, ProposalDraft, PromptTemplate


def test_prompt_template_unique_name_version():
    idx = {i.name for i in PromptTemplate.__table__.indexes}
    assert any("ix_prompt_templates_name_version" in name for name in idx)


def test_proposal_draft_fks():
    cols = ProposalDraft.__table__.columns
    assert "template_id" in cols
    assert "context_hash" in cols
    assert "rendered_system" in cols
    assert "rendered_user" in cols


def test_decision_review_result_column():
    cols = DecisionReview.__table__.columns
    assert "decision_id" in cols
    assert "reviewer_type" in cols
    assert "result" in cols
    assert "adjustments_json" in cols


def test_agent_invocation_core_columns():
    cols = set(AgentInvocation.__table__.columns.keys())
    assert {
        "agent_type", "input_hash", "prompt_template_id",
        "llm_provider", "llm_model", "tokens_used", "latency_ms",
        "outcome",
    } <= cols
```

- [ ] **Step 3.2: Run tests and verify failure**

Run: `cd backend && .venv/bin/pytest -q tests/unit/models/test_decision_audit_models.py`
Expected: `ImportError: cannot import name 'PromptTemplate'`.

- [ ] **Step 3.3: Write the migration**

Create `backend/migrations/versions/20260421_0003_decision_audit_schema.py`:

```python
"""decision audit schema: prompt_templates, proposal_drafts, decision_reviews, agent_invocations

Revision ID: 20260421_0003
Revises: 20260421_0002
Create Date: 2026-04-21 00:00:02.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0003"
down_revision: Union[str, Sequence[str], None] = "20260421_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("system_template", sa.Text(), nullable=False),
        sa.Column("user_template", sa.Text(), nullable=False),
        sa.Column("variables_json", sa.JSON(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    op.create_index("ix_prompt_templates_name_version", "prompt_templates", ["name", "version"], unique=True)

    op.create_table(
        "proposal_drafts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("template_id", sa.BigInteger(), nullable=True),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column("rendered_system", sa.Text(), nullable=False),
        sa.Column("rendered_user", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_proposal_drafts_account"),
        sa.ForeignKeyConstraint(["template_id"], ["prompt_templates.id"], name="fk_proposal_drafts_template"),
    )

    op.create_table(
        "decision_reviews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("decision_id", sa.BigInteger(), nullable=False),
        sa.Column("reviewer_type", sa.String(length=20), nullable=False),  # rule | ai
        sa.Column("result", sa.String(length=20), nullable=False),  # approve | adjust | reject
        sa.Column("adjustments_json", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["decision_id"], ["ai_decisions.id"], name="fk_decision_reviews_decision"),
    )

    op.create_table(
        "agent_invocations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("agent_type", sa.String(length=30), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("prompt_template_id", sa.BigInteger(), nullable=True),
        sa.Column("llm_provider", sa.String(length=30), nullable=True),
        sa.Column("llm_model", sa.String(length=60), nullable=True),
        sa.Column("input_json", sa.JSON(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_agent_invocations_account"),
    )
    op.create_index("ix_agent_invocations_occurred_at", "agent_invocations", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_invocations_occurred_at", table_name="agent_invocations")
    op.drop_table("agent_invocations")
    op.drop_table("decision_reviews")
    op.drop_table("proposal_drafts")
    op.drop_index("ix_prompt_templates_name_version", table_name="prompt_templates")
    op.drop_table("prompt_templates")
```

- [ ] **Step 3.4: Write the three model files + update `__init__.py`**

Create `backend/src/shared/models/prompt.py`:

```python
from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    system_template: Mapped[str] = mapped_column(Text, nullable=False)
    user_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables_json: Mapped[dict | None] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger)


class ProposalDraft(Base, TimestampMixin):
    __tablename__ = "proposal_drafts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    template_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("prompt_templates.id"))
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    rendered_system: Mapped[str] = mapped_column(Text, nullable=False)
    rendered_user: Mapped[str] = mapped_column(Text, nullable=False)
```

Create `backend/src/shared/models/decision_review.py`:

```python
from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class DecisionReview(Base, TimestampMixin):
    __tablename__ = "decision_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ai_decisions.id"), nullable=False)
    reviewer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    adjustments_json: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
```

Create `backend/src/shared/models/agent_invocation.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class AgentInvocation(Base, TimestampMixin):
    __tablename__ = "agent_invocations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_template_id: Mapped[int | None] = mapped_column(BigInteger)
    llm_provider: Mapped[str | None] = mapped_column(String(30))
    llm_model: Mapped[str | None] = mapped_column(String(60))
    input_json: Mapped[dict | None] = mapped_column(JSON)
    output_json: Mapped[dict | None] = mapped_column(JSON)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    error: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

Update `backend/src/shared/models/__init__.py`:

```python
from src.shared.models.prompt import PromptTemplate, ProposalDraft
from src.shared.models.decision_review import DecisionReview
from src.shared.models.agent_invocation import AgentInvocation
```

Add `"PromptTemplate", "ProposalDraft", "DecisionReview", "AgentInvocation"` to `__all__`.

- [ ] **Step 3.5: Run tests; expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_decision_audit_models.py
```

- [ ] **Step 3.6: Commit + push**

```bash
git add backend/migrations/versions/20260421_0003_decision_audit_schema.py \
        backend/src/shared/models/prompt.py \
        backend/src/shared/models/decision_review.py \
        backend/src/shared/models/agent_invocation.py \
        backend/src/shared/models/__init__.py \
        backend/tests/unit/models/test_decision_audit_models.py
git commit -m "foundation(plan1): add decision audit schema (prompt_templates, proposal_drafts, decision_reviews, agent_invocations)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 4: Insight Schema (experiences + experience_summaries + trade_attributions + strategy_scores)

**Goal:** Create V0.2+ insight tables. `experiences` (new v2 table alongside existing `experience_store` for migration path), `experience_summaries` is stubbed WITHOUT the `embedding` column (pgvector deferred to V0.2 per spec §8.2), the other two are empty placeholders.

**Files:**
- Create: `backend/migrations/versions/20260421_0004_insight_schema.py`
- Create: `backend/src/shared/models/experience_v2.py`
- Create: `backend/src/shared/models/attribution.py`
- Modify: `backend/src/shared/models/__init__.py`
- Create test: `backend/tests/unit/models/test_insight_models.py`

### Steps

- [ ] **Step 4.1: Write failing test**

Create `backend/tests/unit/models/test_insight_models.py`:

```python
from __future__ import annotations

from src.shared.models import (
    ExperienceSummary, ExperienceV2, StrategyScore, TradeAttribution,
)


def test_experience_v2_columns():
    cols = set(ExperienceV2.__table__.columns.keys())
    assert {
        "account_id", "trade_id", "symbol", "regime_at_open",
        "strategy_mode", "factor_snapshot_at_open_id", "pnl_pct",
        "hold_duration", "exit_reason",
    } <= cols


def test_experience_summary_has_no_embedding_in_v01():
    cols = set(ExperienceSummary.__table__.columns.keys())
    assert "summary_text" in cols
    assert "embedding" not in cols, "pgvector deferred to V0.2"


def test_trade_attribution_columns():
    cols = set(TradeAttribution.__table__.columns.keys())
    assert {
        "trade_id", "by_symbol", "by_time_bucket", "by_exit_reason",
        "by_factors_json", "factor_contributions_json",
    } <= cols


def test_strategy_score_composite_key_columns():
    cols = set(StrategyScore.__table__.columns.keys())
    assert {"strategy_mode", "symbol", "regime", "window", "win_rate", "sharpe"} <= cols
```

- [ ] **Step 4.2: Run, verify failure**

`cd backend && .venv/bin/pytest -q tests/unit/models/test_insight_models.py`

- [ ] **Step 4.3: Write migration**

Create `backend/migrations/versions/20260421_0004_insight_schema.py`:

```python
"""insight schema: experiences (v2), experience_summaries, trade_attributions, strategy_scores

Revision ID: 20260421_0004
Revises: 20260421_0003
Create Date: 2026-04-21 00:00:03.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0004"
down_revision: Union[str, Sequence[str], None] = "20260421_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    # experiences (v2). Kept separate from legacy experience_store; V0.2 migration may merge.
    op.create_table(
        "experiences",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("trade_id", sa.BigInteger(), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("regime_at_open", sa.String(length=20), nullable=True),
        sa.Column("strategy_mode", sa.String(length=30), nullable=True),
        sa.Column("factor_snapshot_at_open_id", sa.BigInteger(), nullable=True),
        sa.Column("pnl_pct", sa.Numeric(10, 6), nullable=True),
        sa.Column("hold_duration", sa.Integer(), nullable=True),  # seconds
        sa.Column("exit_reason", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_experiences_account"),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], name="fk_experiences_trade"),
    )

    # experience_summaries — V0.2+ (embedding column added later when pgvector is introduced).
    op.create_table(
        "experience_summaries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("experience_id", sa.BigInteger(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("generated_by_agent", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["experience_id"], ["experiences.id"], name="fk_experience_summaries_experience"),
    )

    # trade_attributions — V0.2+
    op.create_table(
        "trade_attributions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trade_id", sa.BigInteger(), nullable=False),
        sa.Column("by_symbol", sa.JSON(), nullable=True),
        sa.Column("by_time_bucket", sa.String(length=40), nullable=True),
        sa.Column("by_exit_reason", sa.String(length=30), nullable=True),
        sa.Column("by_factors_json", sa.JSON(), nullable=True),
        sa.Column("factor_contributions_json", sa.JSON(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], name="fk_trade_attributions_trade"),
    )

    # strategy_scores — V0.2+
    op.create_table(
        "strategy_scores",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("strategy_mode", sa.String(length=30), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("regime", sa.String(length=20), nullable=False),
        sa.Column("window", sa.String(length=10), nullable=False),  # 7d | 30d
        sa.Column("win_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("pnl_sum", sa.Numeric(20, 8), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(10, 6), nullable=True),
        sa.Column("sharpe", sa.Numeric(8, 4), nullable=True),
        sa.Column("false_breakout_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("regime_fit_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_strategy_scores_account"),
    )
    op.create_index(
        "ix_strategy_scores_key",
        "strategy_scores",
        ["account_id", "strategy_mode", "symbol", "regime", "window"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_strategy_scores_key", table_name="strategy_scores")
    op.drop_table("strategy_scores")
    op.drop_table("trade_attributions")
    op.drop_table("experience_summaries")
    op.drop_table("experiences")
```

- [ ] **Step 4.4: Write model files**

Create `backend/src/shared/models/experience_v2.py`:

```python
from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class ExperienceV2(Base, TimestampMixin):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    trading_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="testnet")
    trade_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("trades.id"))
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    regime_at_open: Mapped[str | None] = mapped_column(String(20))
    strategy_mode: Mapped[str | None] = mapped_column(String(30))
    factor_snapshot_at_open_id: Mapped[int | None] = mapped_column(BigInteger)
    pnl_pct: Mapped[float | None] = mapped_column(Numeric(10, 6))
    hold_duration: Mapped[int | None] = mapped_column(Integer)
    exit_reason: Mapped[str | None] = mapped_column(String(30))


class ExperienceSummary(Base, TimestampMixin):
    __tablename__ = "experience_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    experience_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("experiences.id"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[dict | None] = mapped_column(JSON)
    generated_by_agent: Mapped[str | None] = mapped_column(String(40))
```

Create `backend/src/shared/models/attribution.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class TradeAttribution(Base, TimestampMixin):
    __tablename__ = "trade_attributions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("trades.id"), nullable=False)
    by_symbol: Mapped[dict | None] = mapped_column(JSON)
    by_time_bucket: Mapped[str | None] = mapped_column(String(40))
    by_exit_reason: Mapped[str | None] = mapped_column(String(30))
    by_factors_json: Mapped[dict | None] = mapped_column(JSON)
    factor_contributions_json: Mapped[dict | None] = mapped_column(JSON)
    narrative: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StrategyScore(Base, TimestampMixin):
    __tablename__ = "strategy_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("accounts.id"), nullable=False, default=1)
    strategy_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    regime: Mapped[str] = mapped_column(String(20), nullable=False)
    window: Mapped[str] = mapped_column(String(10), nullable=False)
    win_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    pnl_sum: Mapped[float | None] = mapped_column(Numeric(20, 8))
    max_drawdown: Mapped[float | None] = mapped_column(Numeric(10, 6))
    sharpe: Mapped[float | None] = mapped_column(Numeric(8, 4))
    false_breakout_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    regime_fit_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

Update `backend/src/shared/models/__init__.py`:

```python
from src.shared.models.experience_v2 import ExperienceV2, ExperienceSummary
from src.shared.models.attribution import TradeAttribution, StrategyScore
```

Add `"ExperienceV2", "ExperienceSummary", "TradeAttribution", "StrategyScore"` to `__all__`.

- [ ] **Step 4.5: Run tests, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_insight_models.py
```

- [ ] **Step 4.6: Commit + push**

```bash
git add backend/migrations/versions/20260421_0004_insight_schema.py \
        backend/src/shared/models/experience_v2.py \
        backend/src/shared/models/attribution.py \
        backend/src/shared/models/__init__.py \
        backend/tests/unit/models/test_insight_models.py
git commit -m "foundation(plan1): add insight schema (experiences v2, summaries, attributions, scores)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 5: Shadow + Ops Schema (shadow_decisions + shadow_evaluations + ops_diagnoses)

**Goal:** V0.3+ placeholder tables per spec §6.6. Empty in V0.1, filled by Shadow Runner / Ops AI later.

**Files:**
- Create: `backend/migrations/versions/20260421_0005_shadow_ops_schema.py`
- Create: `backend/src/shared/models/shadow.py`
- Create: `backend/src/shared/models/ops_diagnosis.py`
- Modify: `backend/src/shared/models/__init__.py`
- Create test: `backend/tests/unit/models/test_shadow_ops_models.py`

### Steps

- [ ] **Step 5.1: Write failing test**

Create `backend/tests/unit/models/test_shadow_ops_models.py`:

```python
from __future__ import annotations

from src.shared.models import OpsDiagnosis, ShadowDecision, ShadowEvaluation


def test_shadow_decision_columns():
    cols = set(ShadowDecision.__table__.columns.keys())
    assert {"shadow_run_id", "real_decision_id", "proposal_json", "parameter_version_id"} <= cols


def test_shadow_evaluation_columns():
    cols = set(ShadowEvaluation.__table__.columns.keys())
    assert {"shadow_decision_id", "real_trade_id", "shadow_pnl_sim", "real_pnl", "diff"} <= cols


def test_ops_diagnosis_columns():
    cols = set(OpsDiagnosis.__table__.columns.keys())
    assert {"triggered_by_event_id", "severity", "pattern_matched", "llm_narrative"} <= cols
```

- [ ] **Step 5.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_shadow_ops_models.py
```

- [ ] **Step 5.3: Migration**

Create `backend/migrations/versions/20260421_0005_shadow_ops_schema.py`:

```python
"""shadow + ops schema: shadow_decisions, shadow_evaluations, ops_diagnoses

Revision ID: 20260421_0005
Revises: 20260421_0004
Create Date: 2026-04-21 00:00:04.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0005"
down_revision: Union[str, Sequence[str], None] = "20260421_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "shadow_decisions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shadow_run_id", sa.String(length=64), nullable=False),
        sa.Column("real_decision_id", sa.BigInteger(), nullable=True),
        sa.Column("proposal_json", sa.JSON(), nullable=False),
        sa.Column("parameter_version_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["real_decision_id"], ["ai_decisions.id"], name="fk_shadow_decisions_real"),
        sa.ForeignKeyConstraint(["parameter_version_id"], ["parameter_versions.id"], name="fk_shadow_decisions_param"),
    )

    op.create_table(
        "shadow_evaluations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shadow_decision_id", sa.BigInteger(), nullable=False),
        sa.Column("real_trade_id", sa.BigInteger(), nullable=True),
        sa.Column("shadow_pnl_sim", sa.Numeric(20, 8), nullable=True),
        sa.Column("real_pnl", sa.Numeric(20, 8), nullable=True),
        sa.Column("diff", sa.Numeric(20, 8), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["shadow_decision_id"], ["shadow_decisions.id"], name="fk_shadow_evaluations_shadow"),
        sa.ForeignKeyConstraint(["real_trade_id"], ["trades.id"], name="fk_shadow_evaluations_real"),
    )

    op.create_table(
        "ops_diagnoses",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("triggered_by_event_id", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("pattern_matched", sa.String(length=100), nullable=True),
        sa.Column("llm_narrative", sa.Text(), nullable=True),
        sa.Column("recommendations_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )


def downgrade() -> None:
    op.drop_table("ops_diagnoses")
    op.drop_table("shadow_evaluations")
    op.drop_table("shadow_decisions")
```

- [ ] **Step 5.4: Models**

Create `backend/src/shared/models/shadow.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class ShadowDecision(Base, TimestampMixin):
    __tablename__ = "shadow_decisions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shadow_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    real_decision_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("ai_decisions.id"))
    proposal_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    parameter_version_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("parameter_versions.id"))


class ShadowEvaluation(Base, TimestampMixin):
    __tablename__ = "shadow_evaluations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shadow_decision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("shadow_decisions.id"), nullable=False)
    real_trade_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("trades.id"))
    shadow_pnl_sim: Mapped[float | None] = mapped_column(Numeric(20, 8))
    real_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8))
    diff: Mapped[float | None] = mapped_column(Numeric(20, 8))
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

Create `backend/src/shared/models/ops_diagnosis.py`:

```python
from __future__ import annotations

from sqlalchemy import BigInteger, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class OpsDiagnosis(Base, TimestampMixin):
    __tablename__ = "ops_diagnoses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    triggered_by_event_id: Mapped[str | None] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    pattern_matched: Mapped[str | None] = mapped_column(String(100))
    llm_narrative: Mapped[str | None] = mapped_column(Text)
    recommendations_json: Mapped[dict | None] = mapped_column(JSON)
```

Update `backend/src/shared/models/__init__.py`:

```python
from src.shared.models.shadow import ShadowDecision, ShadowEvaluation
from src.shared.models.ops_diagnosis import OpsDiagnosis
```

Add to `__all__`.

- [ ] **Step 5.5: Run, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_shadow_ops_models.py
```

- [ ] **Step 5.6: Commit + push**

```bash
git add backend/migrations/versions/20260421_0005_shadow_ops_schema.py \
        backend/src/shared/models/shadow.py \
        backend/src/shared/models/ops_diagnosis.py \
        backend/src/shared/models/__init__.py \
        backend/tests/unit/models/test_shadow_ops_models.py
git commit -m "foundation(plan1): add shadow mode + ops diagnosis placeholder tables

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 6: Extend `ai_decisions` with New Columns

**Goal:** Add columns to `ai_decisions` per spec §6.6 so the V0.1 AIT Pipeline can record LLM metadata, source, and links to `proposal_drafts` / `factor_snapshots`.

**New columns**: `proposal_draft_id BIGINT NULL`, `llm_provider VARCHAR(30) NULL`, `llm_model VARCHAR(60) NULL`, `tokens_used INT NULL`, `latency_ms INT NULL`, `source VARCHAR(20) NOT NULL DEFAULT 'ai_trader'`, `factor_snapshot_id BIGINT NULL`.

**Files:**
- Create: `backend/migrations/versions/20260421_0006_extend_ai_decisions.py`
- Modify: `backend/src/shared/models/decision.py`
- Create test: `backend/tests/unit/models/test_ai_decision_extended.py`

### Steps

- [ ] **Step 6.1: Write failing test**

Create `backend/tests/unit/models/test_ai_decision_extended.py`:

```python
from __future__ import annotations

from src.shared.models import AIDecision


def test_ai_decision_has_extended_columns():
    cols = set(AIDecision.__table__.columns.keys())
    required = {
        "proposal_draft_id",
        "llm_provider",
        "llm_model",
        "tokens_used",
        "latency_ms",
        "source",
        "factor_snapshot_id",
    }
    missing = required - cols
    assert not missing, f"missing columns: {missing}"


def test_source_default_is_ai_trader():
    col = AIDecision.__table__.columns["source"]
    # default may be ColumnDefault or server_default wrapping.
    assert "ai_trader" in str(col.default.arg) or "ai_trader" in str(col.server_default.arg)
```

- [ ] **Step 6.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_ai_decision_extended.py
```

- [ ] **Step 6.3: Migration**

Create `backend/migrations/versions/20260421_0006_extend_ai_decisions.py`:

```python
"""extend ai_decisions with proposal_draft_id, llm metadata, source, factor_snapshot_id

Revision ID: 20260421_0006
Revises: 20260421_0005
Create Date: 2026-04-21 00:00:05.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0006"
down_revision: Union[str, Sequence[str], None] = "20260421_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_decisions", sa.Column("proposal_draft_id", sa.BigInteger(), nullable=True))
    op.add_column("ai_decisions", sa.Column("llm_provider", sa.String(length=30), nullable=True))
    op.add_column("ai_decisions", sa.Column("llm_model", sa.String(length=60), nullable=True))
    op.add_column("ai_decisions", sa.Column("tokens_used", sa.Integer(), nullable=True))
    op.add_column("ai_decisions", sa.Column("latency_ms", sa.Integer(), nullable=True))
    op.add_column(
        "ai_decisions",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="ai_trader"),
    )
    op.add_column("ai_decisions", sa.Column("factor_snapshot_id", sa.BigInteger(), nullable=True))

    op.create_foreign_key(
        "fk_ai_decisions_proposal_draft",
        "ai_decisions",
        "proposal_drafts",
        ["proposal_draft_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_ai_decisions_factor_snapshot",
        "ai_decisions",
        "factor_snapshots",
        ["factor_snapshot_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_decisions_factor_snapshot", "ai_decisions", type_="foreignkey")
    op.drop_constraint("fk_ai_decisions_proposal_draft", "ai_decisions", type_="foreignkey")
    op.drop_column("ai_decisions", "factor_snapshot_id")
    op.drop_column("ai_decisions", "source")
    op.drop_column("ai_decisions", "latency_ms")
    op.drop_column("ai_decisions", "tokens_used")
    op.drop_column("ai_decisions", "llm_model")
    op.drop_column("ai_decisions", "llm_provider")
    op.drop_column("ai_decisions", "proposal_draft_id")
```

- [ ] **Step 6.4: Update model**

Edit `backend/src/shared/models/decision.py`, add these columns after `is_fallback` (and add imports for `Integer`, `ForeignKey`):

```python
proposal_draft_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("proposal_drafts.id"))
llm_provider: Mapped[str | None] = mapped_column(String(30))
llm_model: Mapped[str | None] = mapped_column(String(60))
tokens_used: Mapped[int | None] = mapped_column(Integer)
latency_ms: Mapped[int | None] = mapped_column(Integer)
source: Mapped[str] = mapped_column(String(20), nullable=False, default="ai_trader")
factor_snapshot_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("factor_snapshots.id"))
```

- [ ] **Step 6.5: Run tests, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_ai_decision_extended.py
```

- [ ] **Step 6.6: Commit + push**

```bash
git add backend/migrations/versions/20260421_0006_extend_ai_decisions.py \
        backend/src/shared/models/decision.py \
        backend/tests/unit/models/test_ai_decision_extended.py
git commit -m "foundation(plan1): extend ai_decisions with proposal_draft, llm metadata, source, factor_snapshot links

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 7: UUIDv7 Utility

**Goal:** Event IDs use UUIDv7 (time-ordered) for natural ordering in Redis Streams and DB. Wrap the `uuid6` library to centralize.

**Files:**
- Modify: `backend/pyproject.toml` (add `uuid6>=2024.1.12` dependency)
- Create: `backend/src/events/__init__.py`
- Create: `backend/src/events/ids.py`
- Create test: `backend/tests/unit/events/test_ids.py`

### Steps

- [ ] **Step 7.1: Add `uuid6` dependency**

Edit `backend/pyproject.toml`, add to `dependencies`:

```
"uuid6>=2024.7.10",
```

Then:

```bash
cd backend && .venv/bin/pip install -e '.[dev]'
# OR if using uv:
# uv sync --extra dev
```

- [ ] **Step 7.2: Write failing test**

Create `backend/tests/unit/events/test_ids.py`:

```python
from __future__ import annotations

import time
import uuid

from src.events.ids import new_event_id, parse_event_id


def test_new_event_id_is_uuid_v7_shape():
    eid = new_event_id()
    parsed = uuid.UUID(eid)
    assert parsed.version == 7


def test_event_ids_are_time_ordered():
    first = new_event_id()
    time.sleep(0.002)
    second = new_event_id()
    assert first < second, "UUIDv7 ids must be lexicographically time-ordered"


def test_parse_event_id_roundtrip():
    eid = new_event_id()
    parsed = parse_event_id(eid)
    assert str(parsed) == eid
```

- [ ] **Step 7.3: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_ids.py
```

- [ ] **Step 7.4: Implement**

Create `backend/src/events/__init__.py`:

```python
"""AlphaPilot event bus primitives: IDs, contracts, bus, outbox, inbox."""
```

Create `backend/src/events/ids.py`:

```python
"""UUIDv7 wrappers. Centralized so the underlying library can be swapped.

Event IDs are time-ordered so Redis Streams / DB queries sort naturally.
"""
from __future__ import annotations

import uuid

import uuid6


def new_event_id() -> str:
    """Generate a new UUIDv7 as a string (canonical hex form with dashes)."""
    return str(uuid6.uuid7())


def parse_event_id(value: str) -> uuid.UUID:
    """Parse an event id; raises ValueError if invalid or not UUIDv7."""
    parsed = uuid.UUID(value)
    if parsed.version != 7:
        raise ValueError(f"expected UUIDv7, got v{parsed.version}")
    return parsed
```

Create `backend/tests/unit/events/__init__.py` (empty file, marks package).

- [ ] **Step 7.5: Run, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_ids.py
```

- [ ] **Step 7.6: Commit + push**

```bash
git add backend/pyproject.toml \
        backend/src/events/__init__.py \
        backend/src/events/ids.py \
        backend/tests/unit/events/__init__.py \
        backend/tests/unit/events/test_ids.py
git commit -m "foundation(plan1): add UUIDv7 event id utility

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 8: Event Contracts Module

**Goal:** Define every event dataclass per spec §3.3. Pydantic v2 models (not `@dataclass`) so JSON serialization and schema versioning are free. Only V0.1 ★ events are actually published by this plan's code; others are defined for forward-compatibility.

**Files:**
- Create: `backend/src/events/contracts.py`
- Create test: `backend/tests/unit/events/test_contracts.py`

### Steps

- [ ] **Step 8.1: Write failing test**

Create `backend/tests/unit/events/test_contracts.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from src.events.contracts import (
    CandleClosed, CircuitBreakerTriggered, DecisionProposed, DecisionRejected,
    DecisionReviewed, EventEnvelope, IndicatorsComputed, OrderFailed,
    OrderFilled, OrderSubmitted, PositionClosed, PositionOpened,
    PositionUpdated, RegimeClassified, RiskEventTriggered, TradeClosed,
)


def test_envelope_required_fields():
    env = EventEnvelope(
        event_id="0190e6a6-0000-7000-8000-000000000000",
        account_id=1,
        trading_mode="testnet",
        occurred_at=datetime.now(timezone.utc),
        trace_id="abc",
        schema_version=1,
        event_type="candle.closed",
        payload={},
    )
    assert env.schema_version == 1


def test_candle_closed_payload():
    evt = CandleClosed(
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1.0, high=1.1, low=0.9, close=1.05, volume=100.0,
    )
    data = evt.model_dump()
    assert data["symbol"] == "BTCUSDT"


def test_decision_proposed_has_all_required_fields():
    from src.events.contracts import DecisionProposed
    evt = DecisionProposed(
        decision_id=42, symbol="BTCUSDT", timeframe="1h",
        action="OPEN_LONG", confidence=0.7,
        source="ai_trader", strategy_mode="ai_trend",
        is_fallback=False,
    )
    assert evt.action == "OPEN_LONG"


def test_envelope_type_check_matches_registry():
    """Every event class should be registered with a type string."""
    from src.events.contracts import EVENT_TYPE_REGISTRY
    assert "candle.closed" in EVENT_TYPE_REGISTRY
    assert "decision.proposed" in EVENT_TYPE_REGISTRY
    assert EVENT_TYPE_REGISTRY["candle.closed"] is CandleClosed
```

- [ ] **Step 8.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_contracts.py
```

- [ ] **Step 8.3: Implement**

Create `backend/src/events/contracts.py`:

```python
"""Event contracts per spec §3.3.

Every event is a Pydantic BaseModel. Envelope wraps an event for transport
across Redis Streams; individual event classes describe the payload only.

Version 1 of the schema — increment `schema_version` on any breaking change.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Envelope
# ------------------------------------------------------------------

class EventEnvelope(BaseModel):
    """Transport envelope; payload is the serialized form of one of the event classes below."""

    event_id: str  # UUIDv7
    account_id: int = 1
    trading_mode: str = "testnet"
    occurred_at: datetime
    trace_id: str
    schema_version: int = 1
    event_type: str
    payload: dict[str, Any]


# ------------------------------------------------------------------
# Base for all event payload classes (so we can register them)
# ------------------------------------------------------------------

class _Event(BaseModel):
    """Marker base. Subclasses set `event_type` as ClassVar."""

    event_type: ClassVar[str] = "_unset"


# ------------------------------------------------------------------
# market.*
# ------------------------------------------------------------------

class CandleClosed(_Event):
    event_type: ClassVar[str] = "candle.closed"
    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


# ------------------------------------------------------------------
# factor.*
# ------------------------------------------------------------------

class IndicatorsComputed(_Event):
    event_type: ClassVar[str] = "indicators.computed"
    symbol: str
    timeframe: str
    open_time: datetime
    indicator_snapshot_id: int


class FactorsUpdated(_Event):
    event_type: ClassVar[str] = "factors.updated"
    symbol: str
    timeframe: str
    open_time: datetime
    factor_snapshot_id: int


class RegimeClassified(_Event):
    event_type: ClassVar[str] = "regime.classified"
    symbol: str
    timeframe: str
    open_time: datetime
    regime: Literal["trending_up", "trending_down", "ranging", "chaotic"]
    confidence: float


# ------------------------------------------------------------------
# decision.*
# ------------------------------------------------------------------

class ProposalDrafted(_Event):
    event_type: ClassVar[str] = "proposal.drafted"
    proposal_draft_id: int
    symbol: str
    timeframe: str
    template_id: int | None = None


class DecisionProposed(_Event):
    event_type: ClassVar[str] = "decision.proposed"
    decision_id: int
    symbol: str
    timeframe: str
    action: Literal["OPEN_LONG", "CLOSE_LONG", "HOLD"]
    confidence: float
    source: Literal["ai_trader", "program_trader", "shadow", "manual"]
    strategy_mode: str | None = None
    is_fallback: bool = False


class DecisionReviewed(_Event):
    event_type: ClassVar[str] = "decision.reviewed"
    decision_id: int
    review_id: int
    result: Literal["approve", "adjust", "reject"]


class DecisionDegraded(_Event):
    event_type: ClassVar[str] = "decision.degraded"
    decision_id: int
    original_action: str
    modified_action: str
    reason: str


class DecisionRejected(_Event):
    event_type: ClassVar[str] = "decision.rejected"
    decision_id: int
    reason: str


# ------------------------------------------------------------------
# order.*
# ------------------------------------------------------------------

class OrderSubmitted(_Event):
    event_type: ClassVar[str] = "order.submitted"
    order_id: int
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    quantity: float
    price: float | None = None
    trace_id: str


class OrderFilled(_Event):
    event_type: ClassVar[str] = "order.filled"
    order_id: int
    symbol: str
    filled_quantity: float
    avg_fill_price: float


class OrderFailed(_Event):
    event_type: ClassVar[str] = "order.failed"
    order_id: int
    reason: str


# ------------------------------------------------------------------
# position.*
# ------------------------------------------------------------------

class PositionOpened(_Event):
    event_type: ClassVar[str] = "position.opened"
    position_id: int
    symbol: str
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float | None = None


class PositionUpdated(_Event):
    event_type: ClassVar[str] = "position.updated"
    position_id: int
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PositionClosed(_Event):
    event_type: ClassVar[str] = "position.closed"
    position_id: int
    exit_price: float
    exit_reason: str


# ------------------------------------------------------------------
# trade.*
# ------------------------------------------------------------------

class TradeClosed(_Event):
    event_type: ClassVar[str] = "trade.closed"
    trade_id: int
    symbol: str
    pnl: float
    pnl_pct: float
    exit_reason: str


# ------------------------------------------------------------------
# risk.*
# ------------------------------------------------------------------

class RiskEventTriggered(_Event):
    event_type: ClassVar[str] = "risk.event.triggered"
    risk_event_id: int
    event_subtype: str
    severity: Literal["info", "warn", "critical"] = "warn"
    symbol: str | None = None


class CircuitBreakerTriggered(_Event):
    event_type: ClassVar[str] = "circuit_breaker.triggered"
    reason: str


class ManualOverride(_Event):
    event_type: ClassVar[str] = "manual.override"
    operator_user_id: int
    action: str
    target: str
    reason: str | None = None


# ------------------------------------------------------------------
# control.*  (commands — Control Plane → Execution Core)
# ------------------------------------------------------------------

class ControlCommand(_Event):
    event_type: ClassVar[str] = "control.command"
    command: Literal["pause_trading", "resume_trading", "close_position", "close_all", "unlock_breaker"]
    operator_user_id: int
    target_position_id: int | None = None
    reason: str | None = None


# ------------------------------------------------------------------
# learn.*  (V0.3+ — defined for forward compat)
# ------------------------------------------------------------------

class ParamsCandidateProposed(_Event):
    event_type: ClassVar[str] = "params.candidate.proposed"
    parameter_version_id: int


class ParamsCandidateValidated(_Event):
    event_type: ClassVar[str] = "params.candidate.validated"
    parameter_version_id: int
    validation_summary: dict[str, Any]


class ParamsApplied(_Event):
    event_type: ClassVar[str] = "params.applied"
    parameter_version_id: int


class ParamsRolledBack(_Event):
    event_type: ClassVar[str] = "params.rolled_back"
    parameter_version_id: int
    reason: str


# ------------------------------------------------------------------
# ops.*  (V0.3+)
# ------------------------------------------------------------------

class OpsDiagnosis(_Event):
    event_type: ClassVar[str] = "ops.diagnosis"
    diagnosis_id: int
    severity: Literal["info", "warn", "critical"]


class OpsHeartbeat(_Event):
    event_type: ClassVar[str] = "ops.heartbeat"
    service: str
    uptime_seconds: int


# ------------------------------------------------------------------
# Registry — string → class, used by consumers to parse envelopes
# ------------------------------------------------------------------

def _all_event_classes() -> list[type[_Event]]:
    return [
        CandleClosed,
        IndicatorsComputed, FactorsUpdated, RegimeClassified,
        ProposalDrafted, DecisionProposed, DecisionReviewed,
        DecisionDegraded, DecisionRejected,
        OrderSubmitted, OrderFilled, OrderFailed,
        PositionOpened, PositionUpdated, PositionClosed,
        TradeClosed,
        RiskEventTriggered, CircuitBreakerTriggered, ManualOverride,
        ControlCommand,
        ParamsCandidateProposed, ParamsCandidateValidated,
        ParamsApplied, ParamsRolledBack,
        OpsDiagnosis, OpsHeartbeat,
    ]


EVENT_TYPE_REGISTRY: dict[str, type[_Event]] = {
    cls.event_type: cls for cls in _all_event_classes()
}
```

- [ ] **Step 8.4: Run tests, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_contracts.py
```

- [ ] **Step 8.5: Commit + push**

```bash
git add backend/src/events/contracts.py \
        backend/tests/unit/events/test_contracts.py
git commit -m "foundation(plan1): add event contracts with envelope + registry

Covers V1.0 event catalog from spec §3.3. Only ★ events are published by
V0.1 code; rest are defined for forward compatibility.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 9: event_inbox + event_outbox Tables

**Goal:** Create the two tables that implement Outbox + Inbox idempotency patterns (spec §3.6 / §6.6).

**Files:**
- Create: `backend/migrations/versions/20260421_0007_event_bus_tables.py`
- Create: `backend/src/shared/models/event_store.py`
- Modify: `backend/src/shared/models/__init__.py`
- Create test: `backend/tests/unit/models/test_event_store_models.py`

### Steps

- [ ] **Step 9.1: Write failing test**

Create `backend/tests/unit/models/test_event_store_models.py`:

```python
from __future__ import annotations

from src.shared.models import EventInbox, EventOutbox


def test_event_inbox_unique_constraint():
    idx = {i.name for i in EventInbox.__table__.indexes}
    assert any("consumer_name_event_id" in name for name in idx)


def test_event_outbox_required_fields():
    cols = set(EventOutbox.__table__.columns.keys())
    assert {"aggregate_type", "aggregate_id", "event_type", "payload_json", "published_at"} <= cols
```

- [ ] **Step 9.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_event_store_models.py
```

- [ ] **Step 9.3: Migration**

Create `backend/migrations/versions/20260421_0007_event_bus_tables.py`:

```python
"""event bus tables: event_inbox (idempotent consumption) + event_outbox (atomic publish)

Revision ID: 20260421_0007
Revises: 20260421_0006
Create Date: 2026-04-21 00:00:06.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0007"
down_revision: Union[str, Sequence[str], None] = "20260421_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "event_inbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("consumer_name", sa.String(length=80), nullable=False),
        sa.Column("event_id", sa.String(length=40), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    op.create_index(
        "ix_event_inbox_consumer_name_event_id",
        "event_inbox",
        ["consumer_name", "event_id"],
        unique=True,
    )

    op.create_table(
        "event_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("aggregate_type", sa.String(length=40), nullable=False),
        sa.Column("aggregate_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("event_id", sa.String(length=40), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    # Partial index on unpublished rows — the shuttle worker polls these.
    op.execute(
        "CREATE INDEX ix_event_outbox_unpublished "
        "ON event_outbox (id) WHERE published_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_event_outbox_unpublished")
    op.drop_table("event_outbox")
    op.drop_index("ix_event_inbox_consumer_name_event_id", table_name="event_inbox")
    op.drop_table("event_inbox")
```

- [ ] **Step 9.4: Model**

Create `backend/src/shared/models/event_store.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base, TimestampMixin


class EventInbox(Base, TimestampMixin):
    __tablename__ = "event_inbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    consumer_name: Mapped[str] = mapped_column(String(80), nullable=False)
    event_id: Mapped[str] = mapped_column(String(40), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EventOutbox(Base, TimestampMixin):
    __tablename__ = "event_outbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    aggregate_type: Mapped[str] = mapped_column(String(40), nullable=False)
    aggregate_id: Mapped[int | None] = mapped_column(BigInteger)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_id: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
```

Update `backend/src/shared/models/__init__.py`:

```python
from src.shared.models.event_store import EventInbox, EventOutbox
```

Add to `__all__`.

- [ ] **Step 9.5: Run tests, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/models/test_event_store_models.py
```

- [ ] **Step 9.6: Commit + push**

```bash
git add backend/migrations/versions/20260421_0007_event_bus_tables.py \
        backend/src/shared/models/event_store.py \
        backend/src/shared/models/__init__.py \
        backend/tests/unit/models/test_event_store_models.py
git commit -m "foundation(plan1): add event_inbox (idempotency) + event_outbox (atomic publish) tables

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 10: EventBus Abstract Interface + Redis Streams Adapter

**Goal:** A `EventBus` protocol + a Redis-Streams-backed implementation. Support `publish(envelope)`, `consume(stream, group, consumer) -> iterator`, and `ack(stream, group, message_id)`. In-process fast path is a separate no-transport stub used inside the Pipeline.

**Files:**
- Modify: `backend/pyproject.toml` (add `fakeredis>=2.23.0` to dev deps)
- Create: `backend/src/events/bus.py`
- Create test: `backend/tests/unit/events/test_bus_inmem.py`
- Create test: `backend/tests/integration/test_event_bus_streams.py`

### Steps

- [ ] **Step 10.1: Add `fakeredis` dev dependency**

Edit `backend/pyproject.toml`, add to `[project.optional-dependencies].dev`:

```
"fakeredis>=2.23.0",
```

Then reinstall: `cd backend && .venv/bin/pip install -e '.[dev]'`

- [ ] **Step 10.2: Write failing unit test for in-process bus**

Create `backend/tests/unit/events/test_bus_inmem.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from src.events.bus import InMemoryEventBus
from src.events.contracts import CandleClosed, EventEnvelope
from src.events.ids import new_event_id


def make_envelope(evt: CandleClosed) -> EventEnvelope:
    return EventEnvelope(
        event_id=new_event_id(),
        account_id=1,
        trading_mode="testnet",
        occurred_at=datetime.now(timezone.utc),
        trace_id="t1",
        schema_version=1,
        event_type=evt.event_type,
        payload=evt.model_dump(mode="json"),
    )


def test_inmem_bus_delivers_to_subscribers():
    bus = InMemoryEventBus()
    received: list[EventEnvelope] = []
    bus.subscribe("market.*", received.append)

    evt = CandleClosed(
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1, high=2, low=0.5, close=1.5, volume=100,
    )
    env = make_envelope(evt)
    bus.publish("market.candle", env)

    assert len(received) == 1
    assert received[0].event_type == "candle.closed"


def test_inmem_bus_multiple_subscribers_fan_out():
    bus = InMemoryEventBus()
    a: list[EventEnvelope] = []
    b: list[EventEnvelope] = []
    bus.subscribe("market.*", a.append)
    bus.subscribe("market.*", b.append)

    evt = CandleClosed(
        symbol="X", timeframe="1h", open_time=datetime.now(timezone.utc),
        open=1, high=1, low=1, close=1, volume=1,
    )
    bus.publish("market.candle", make_envelope(evt))
    assert len(a) == 1 and len(b) == 1
```

- [ ] **Step 10.3: Write failing integration test for Redis Streams**

Create `backend/tests/integration/test_event_bus_streams.py`:

```python
"""End-to-end: publish to Redis Streams via RedisStreamsBus, consume with group + ack."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from testcontainers.redis import RedisContainer

from src.events.bus import RedisStreamsBus
from src.events.contracts import CandleClosed, EventEnvelope
from src.events.ids import new_event_id


@pytest.fixture(scope="module")
def redis_url():
    with RedisContainer("redis:7-alpine") as rc:
        yield rc.get_connection_url()


def make_envelope(symbol: str) -> EventEnvelope:
    evt = CandleClosed(
        symbol=symbol, timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1, high=2, low=0.5, close=1.5, volume=100,
    )
    return EventEnvelope(
        event_id=new_event_id(), account_id=1, trading_mode="testnet",
        occurred_at=datetime.now(timezone.utc), trace_id="t1",
        schema_version=1, event_type=evt.event_type,
        payload=evt.model_dump(mode="json"),
    )


def test_publish_and_consume_single_message(redis_url):
    bus = RedisStreamsBus(redis_url)
    bus.ensure_group("market.candle", "test-consumer")

    env = make_envelope("BTCUSDT")
    bus.publish("market.candle", env)

    messages = list(bus.consume("market.candle", "test-consumer", "c1", count=1, block_ms=500))
    assert len(messages) == 1
    msg_id, received = messages[0]
    assert received.event_type == "candle.closed"
    assert received.payload["symbol"] == "BTCUSDT"

    bus.ack("market.candle", "test-consumer", msg_id)
    # Second read should return nothing.
    more = list(bus.consume("market.candle", "test-consumer", "c1", count=1, block_ms=100))
    assert more == []


def test_publish_with_maxlen_trims_old_messages(redis_url):
    bus = RedisStreamsBus(redis_url, default_maxlen=5)
    for i in range(20):
        bus.publish("market.trim", make_envelope(f"SYM{i}"))
    # Stream should have at most ~5 entries (Redis approximate trim).
    import redis as redis_lib
    r = redis_lib.from_url(redis_url, decode_responses=True)
    length = r.xlen("market.trim")
    assert length <= 10, f"expected trim to ~5, got {length}"
```

- [ ] **Step 10.4: Run tests, verify they fail with `ImportError` for `InMemoryEventBus` / `RedisStreamsBus`**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_bus_inmem.py
```

- [ ] **Step 10.5: Implement the bus**

Create `backend/src/events/bus.py`:

```python
"""Event bus abstraction with two backends:

- InMemoryEventBus: in-process, synchronous fan-out. Used by the Pipeline
  fast path (spec §3.1) and in unit tests.
- RedisStreamsBus: persistent, consumer-group-aware. Used for inter-plane
  communication and durable side effects.

Subscribers match by glob patterns (e.g. "market.*", "decision.proposed").
"""
from __future__ import annotations

import fnmatch
import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Iterator, Protocol

import redis as redis_lib

from src.events.contracts import EventEnvelope

logger = logging.getLogger(__name__)


Handler = Callable[[EventEnvelope], None]


class EventBus(Protocol):
    def publish(self, stream: str, envelope: EventEnvelope) -> None: ...


# ------------------------------------------------------------------
# In-memory bus (Pipeline fast path + unit tests)
# ------------------------------------------------------------------

@dataclass
class InMemoryEventBus:
    """Synchronous pub/sub; subscribers matched by fnmatch patterns."""

    _subscribers: list[tuple[str, Handler]] = field(default_factory=list)

    def subscribe(self, pattern: str, handler: Handler) -> None:
        self._subscribers.append((pattern, handler))

    def publish(self, stream: str, envelope: EventEnvelope) -> None:
        for pattern, handler in self._subscribers:
            if fnmatch.fnmatch(stream, pattern) or fnmatch.fnmatch(envelope.event_type, pattern):
                try:
                    handler(envelope)
                except Exception:  # pragma: no cover — isolation between subscribers
                    logger.exception("in-mem handler failed for %s", envelope.event_type)


# ------------------------------------------------------------------
# Redis Streams bus
# ------------------------------------------------------------------

class RedisStreamsBus:
    """Persistent, durable bus backed by Redis Streams.

    Conventions:
      - one stream per event family (e.g. "market.candle", "decision.proposed")
      - consumer groups per downstream service (e.g. "notifier", "attribution")
    """

    def __init__(self, url: str, default_maxlen: int | None = 10_000):
        self._r = redis_lib.from_url(url, decode_responses=True)
        self._default_maxlen = default_maxlen

    def publish(self, stream: str, envelope: EventEnvelope, *, maxlen: int | None = None) -> str:
        """Publish an envelope to a stream. Returns the Redis-assigned message id."""
        effective_maxlen = maxlen if maxlen is not None else self._default_maxlen
        fields = {"envelope": envelope.model_dump_json()}
        if effective_maxlen is not None:
            return self._r.xadd(stream, fields, maxlen=effective_maxlen, approximate=True)
        return self._r.xadd(stream, fields)

    def ensure_group(self, stream: str, group: str) -> None:
        """Create a consumer group if not present. Idempotent."""
        try:
            self._r.xgroup_create(stream, group, id="$", mkstream=True)
        except redis_lib.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def consume(
        self,
        stream: str,
        group: str,
        consumer: str,
        *,
        count: int = 10,
        block_ms: int = 5000,
    ) -> Iterator[tuple[str, EventEnvelope]]:
        """Yield (message_id, envelope) tuples; consumer must ack after processing."""
        streams = {stream: ">"}
        response = self._r.xreadgroup(group, consumer, streams, count=count, block=block_ms)
        if not response:
            return
        for _, messages in response:
            for msg_id, fields in messages:
                raw = fields.get("envelope")
                if raw is None:
                    logger.warning("stream %s msg %s has no envelope", stream, msg_id)
                    continue
                try:
                    env = EventEnvelope.model_validate_json(raw)
                except Exception:
                    logger.exception("failed to parse envelope on %s %s", stream, msg_id)
                    continue
                yield msg_id, env

    def ack(self, stream: str, group: str, message_id: str) -> int:
        return self._r.xack(stream, group, message_id)

    def dead_letter(self, stream: str, envelope: EventEnvelope, reason: str) -> None:
        """Publish to a dead-letter stream `deadletter.<original_stream>`."""
        dl_stream = f"deadletter.{stream}"
        dl_fields = {
            "envelope": envelope.model_dump_json(),
            "original_stream": stream,
            "reason": reason,
        }
        self._r.xadd(dl_stream, dl_fields, maxlen=1_000, approximate=True)
```

- [ ] **Step 10.6: Run tests, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_bus_inmem.py tests/integration/test_event_bus_streams.py
```

- [ ] **Step 10.7: Commit + push**

```bash
git add backend/pyproject.toml \
        backend/src/events/bus.py \
        backend/tests/unit/events/test_bus_inmem.py \
        backend/tests/integration/test_event_bus_streams.py
git commit -m "foundation(plan1): add EventBus abstraction with in-memory + Redis Streams backends

InMemory for Pipeline fast-path, Streams for durable inter-plane comms.
Consumer groups + ack + dead-letter stream supported.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 11: Outbox Writer + Shuttle Worker

**Goal:** `OutboxWriter.record(session, ...)` writes to `event_outbox` inside the caller's DB transaction. Separate worker `EventShuttle` polls unpublished rows every N seconds, publishes to Redis Streams, marks `published_at`.

**Files:**
- Create: `backend/src/events/outbox.py`
- Create: `backend/src/workers/event_shuttle.py`
- Create test: `backend/tests/unit/events/test_outbox.py`
- Create test: `backend/tests/integration/test_event_shuttle.py`

### Steps

- [ ] **Step 11.1: Write failing unit test**

Create `backend/tests/unit/events/test_outbox.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.events.contracts import CandleClosed
from src.events.outbox import OutboxWriter
from src.shared.models import Base, EventOutbox


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_record_writes_unpublished_row(session):
    writer = OutboxWriter()
    evt = CandleClosed(
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=1, high=2, low=0.5, close=1.5, volume=100,
    )
    writer.record(
        session,
        aggregate_type="candle",
        aggregate_id=None,
        event=evt,
        account_id=1,
        trading_mode="testnet",
        trace_id="t1",
    )
    session.commit()

    rows = session.query(EventOutbox).all()
    assert len(rows) == 1
    assert rows[0].event_type == "candle.closed"
    assert rows[0].published_at is None
    # payload_json is the full EventEnvelope dict
    assert rows[0].payload_json["payload"]["symbol"] == "BTCUSDT"
```

- [ ] **Step 11.2: Write failing integration test for the shuttle**

Create `backend/tests/integration/test_event_shuttle.py`:

```python
"""End-to-end: write to event_outbox → shuttle publishes to Redis Streams → consumer sees it."""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from alembic import command
from alembic.config import Config

from src.events.bus import RedisStreamsBus
from src.events.contracts import CandleClosed
from src.events.outbox import OutboxWriter
from src.workers.event_shuttle import EventShuttle


@pytest.fixture(scope="module")
def pg_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        cfg = Config(os.path.join(os.path.dirname(__file__), "../../alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")
        yield url


@pytest.fixture(scope="module")
def redis_url():
    with RedisContainer("redis:7-alpine") as rc:
        yield rc.get_connection_url()


def test_outbox_to_streams_roundtrip(pg_url, redis_url):
    engine = create_engine(pg_url)
    bus = RedisStreamsBus(redis_url)
    bus.ensure_group("candle.closed", "test-group")

    writer = OutboxWriter()
    with Session(engine) as s:
        evt = CandleClosed(
            symbol="BTCUSDT", timeframe="1h",
            open_time=datetime.now(timezone.utc),
            open=1, high=2, low=0.5, close=1.5, volume=100,
        )
        writer.record(s, aggregate_type="candle", aggregate_id=None, event=evt,
                      account_id=1, trading_mode="testnet", trace_id="t1")
        s.commit()

    shuttle = EventShuttle(engine=engine, bus=bus, stream_for_event=lambda e: e)
    published = shuttle.drain_once(batch_size=10)
    assert published == 1

    msgs = list(bus.consume("candle.closed", "test-group", "c1", count=5, block_ms=500))
    assert len(msgs) == 1
    _, env = msgs[0]
    assert env.event_type == "candle.closed"
    assert env.payload["symbol"] == "BTCUSDT"
```

- [ ] **Step 11.3: Run both tests, verify failure**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_outbox.py tests/integration/test_event_shuttle.py
```

- [ ] **Step 11.4: Implement OutboxWriter**

Create `backend/src/events/outbox.py`:

```python
"""Outbox writer — persists events in the same DB transaction as business writes.

Usage pattern inside a service:

    writer = OutboxWriter()
    with Session() as s:
        pos = Position(...)
        s.add(pos)
        s.flush()
        writer.record(s, aggregate_type="position", aggregate_id=pos.id,
                      event=PositionOpened(...), account_id=1,
                      trading_mode="testnet", trace_id=trace_id)
        s.commit()

The `EventShuttle` worker later reads unpublished rows and forwards them
to Redis Streams, marking `published_at`.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.events.contracts import EventEnvelope, _Event
from src.events.ids import new_event_id
from src.shared.models.event_store import EventOutbox


class OutboxWriter:
    """Stateless helper; safe to instantiate per call or as a singleton."""

    def record(
        self,
        session: Session,
        *,
        aggregate_type: str,
        aggregate_id: int | None,
        event: _Event,
        account_id: int = 1,
        trading_mode: str = "testnet",
        trace_id: str,
    ) -> EventOutbox:
        """Attach an event_outbox row to the caller's session (no commit)."""
        event_id = new_event_id()
        envelope = EventEnvelope(
            event_id=event_id,
            account_id=account_id,
            trading_mode=trading_mode,
            occurred_at=datetime.now(timezone.utc),
            trace_id=trace_id,
            schema_version=1,
            event_type=event.event_type,
            payload=event.model_dump(mode="json"),
        )
        row = EventOutbox(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event.event_type,
            event_id=event_id,
            payload_json=envelope.model_dump(mode="json"),
        )
        session.add(row)
        return row
```

- [ ] **Step 11.5: Implement EventShuttle worker**

Create `backend/src/workers/event_shuttle.py`:

```python
"""EventShuttle — moves rows from event_outbox to Redis Streams.

`stream_for_event(event_type)` maps e.g. "candle.closed" → "candle.closed"
(by default identity); override to route all trade.* to the same stream.

Errors increment failed_attempts; after 3 attempts, the envelope goes to
the dead-letter stream and the row is still marked `published_at` so we
don't loop forever.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.events.bus import RedisStreamsBus
from src.events.contracts import EventEnvelope
from src.shared.models.event_store import EventOutbox

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 3


class EventShuttle:
    def __init__(
        self,
        engine: Engine,
        bus: RedisStreamsBus,
        stream_for_event: Callable[[str], str] = lambda t: t,
    ):
        self._engine = engine
        self._bus = bus
        self._stream_for_event = stream_for_event

    def drain_once(self, batch_size: int = 100) -> int:
        """Publish up to `batch_size` unpublished rows. Returns count published."""
        published = 0
        with Session(self._engine) as s:
            rows = (
                s.execute(
                    select(EventOutbox)
                    .where(EventOutbox.published_at.is_(None))
                    .order_by(EventOutbox.id.asc())
                    .limit(batch_size)
                )
                .scalars()
                .all()
            )
            for row in rows:
                try:
                    envelope = EventEnvelope.model_validate(row.payload_json)
                    stream = self._stream_for_event(row.event_type)
                    self._bus.publish(stream, envelope)
                    row.published_at = datetime.now(timezone.utc)
                    published += 1
                except Exception as e:  # noqa: BLE001
                    row.failed_attempts += 1
                    row.last_error = str(e)[:500]
                    logger.exception("shuttle failed for outbox row id=%s", row.id)
                    if row.failed_attempts >= MAX_FAILED_ATTEMPTS:
                        try:
                            envelope = EventEnvelope.model_validate(row.payload_json)
                            self._bus.dead_letter(
                                self._stream_for_event(row.event_type),
                                envelope,
                                reason=row.last_error or "unknown",
                            )
                            row.published_at = datetime.now(timezone.utc)
                        except Exception:
                            logger.exception("dead-letter publish also failed")
            s.commit()
        return published

    def run_forever(self, *, poll_interval_seconds: float = 1.0) -> None:
        while True:
            try:
                self.drain_once()
            except Exception:
                logger.exception("shuttle drain loop error")
            time.sleep(poll_interval_seconds)
```

- [ ] **Step 11.6: Run tests, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_outbox.py tests/integration/test_event_shuttle.py
```

- [ ] **Step 11.7: Commit + push**

```bash
git add backend/src/events/outbox.py \
        backend/src/workers/event_shuttle.py \
        backend/tests/unit/events/test_outbox.py \
        backend/tests/integration/test_event_shuttle.py
git commit -m "foundation(plan1): add OutboxWriter + EventShuttle worker

Implements the transactional Outbox pattern: events written in the same DB
transaction as business state are durably forwarded to Redis Streams.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 12: Inbox Idempotency Helper

**Goal:** Consumer-side helper that records `event_inbox` rows keyed by `(consumer_name, event_id)` so redelivery from Streams doesn't cause double-processing.

**Files:**
- Create: `backend/src/events/inbox.py`
- Create test: `backend/tests/unit/events/test_inbox.py`

### Steps

- [ ] **Step 12.1: Write failing test**

Create `backend/tests/unit/events/test_inbox.py`:

```python
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.events.inbox import InboxGuard
from src.shared.models import Base


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_first_call_returns_true_and_records(session):
    guard = InboxGuard(consumer_name="test")
    assert guard.claim(session, "evt-1") is True
    session.commit()


def test_second_call_with_same_event_returns_false(session):
    guard = InboxGuard(consumer_name="test")
    assert guard.claim(session, "evt-1") is True
    session.commit()
    assert guard.claim(session, "evt-1") is False


def test_different_consumers_can_both_claim_same_event(session):
    a = InboxGuard(consumer_name="a")
    b = InboxGuard(consumer_name="b")
    assert a.claim(session, "evt-1") is True
    session.commit()
    assert b.claim(session, "evt-1") is True
    session.commit()
```

- [ ] **Step 12.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_inbox.py
```

- [ ] **Step 12.3: Implement**

Create `backend/src/events/inbox.py`:

```python
"""Inbox idempotency helper.

Consumer-side guard against redelivery. Usage:

    guard = InboxGuard(consumer_name="notifier")
    for msg_id, env in bus.consume(...):
        with Session() as s:
            if not guard.claim(s, env.event_id):
                bus.ack(...)
                continue
            handle(env)  # business logic
            s.commit()
        bus.ack(...)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.shared.models.event_store import EventInbox


@dataclass
class InboxGuard:
    consumer_name: str

    def claim(self, session: Session, event_id: str) -> bool:
        """Attempt to record (consumer, event_id). Returns True if first-time, False if duplicate.

        Uses a SAVEPOINT (begin_nested) so the caller's other pending changes
        are not rolled back when the unique constraint fires. The outer
        transaction continues normally after a duplicate claim.
        """
        row = EventInbox(
            consumer_name=self.consumer_name,
            event_id=event_id,
            processed_at=datetime.now(timezone.utc),
        )
        sp = session.begin_nested()
        session.add(row)
        try:
            session.flush()
            sp.commit()
            return True
        except IntegrityError:
            sp.rollback()
            return False
```

- [ ] **Step 12.4: Run, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/events/test_inbox.py
```

- [ ] **Step 12.5: Commit + push**

```bash
git add backend/src/events/inbox.py \
        backend/tests/unit/events/test_inbox.py
git commit -m "foundation(plan1): add InboxGuard for idempotent event consumption

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 13: ExchangeAdapter Interface + Types

**Goal:** Abstract `ExchangeAdapter` so `OrderExecutor` never imports `python-binance` directly. Define typed dataclasses for Kline, Ticker, OrderRequest, OrderResult.

**Files:**
- Create: `backend/src/execution/__init__.py`
- Create: `backend/src/execution/exchange/__init__.py`
- Create: `backend/src/execution/exchange/types.py`
- Create: `backend/src/execution/exchange/adapter.py`
- Create test: `backend/tests/unit/execution/__init__.py` (empty)
- Create test: `backend/tests/unit/execution/test_exchange_types.py`

### Steps

- [ ] **Step 13.1: Write failing test**

Create `backend/tests/unit/execution/test_exchange_types.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker


def test_kline_round_trip():
    k = Kline(
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=100.0, high=110.0, low=95.0, close=105.0, volume=1000.0,
    )
    assert k.symbol == "BTCUSDT"


def test_ticker_has_price():
    t = Ticker(symbol="BTCUSDT", price=105.5)
    assert t.price == 105.5


def test_order_request_requires_side_and_qty():
    req = OrderRequest(
        symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.01,
    )
    assert req.quantity == 0.01


def test_exchange_adapter_is_abstract():
    with pytest.raises(TypeError):
        ExchangeAdapter()
```

- [ ] **Step 13.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_exchange_types.py
```

- [ ] **Step 13.3: Create package structure + implement**

Create `backend/src/execution/__init__.py`:

```python
"""Execution Core per spec §5.1."""
```

Create `backend/src/execution/exchange/__init__.py`:

```python
"""Exchange adapter subpackage.

Business code depends only on `ExchangeAdapter` + types; concrete
implementations (BinanceAdapter, future MockAdapter) are swapped via DI.
"""
```

Create `backend/src/execution/exchange/types.py`:

```python
"""Exchange-agnostic value types used by ExchangeAdapter."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Kline(BaseModel):
    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Ticker(BaseModel):
    symbol: str
    price: float
    fetched_at: datetime | None = None


class OrderRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    quantity: float
    price: float | None = None
    client_order_id: str | None = None  # trace_id


class OrderResult(BaseModel):
    exchange_order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    status: Literal["NEW", "FILLED", "PARTIALLY_FILLED", "CANCELED", "REJECTED", "EXPIRED"]
    requested_quantity: float
    filled_quantity: float
    avg_fill_price: float | None = None
    client_order_id: str | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
```

Create `backend/src/execution/exchange/adapter.py`:

```python
"""Abstract ExchangeAdapter. Implementations must not leak exchange-specific types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker


class ExchangeAdapter(ABC):
    """Single abstraction over a spot exchange.

    trading_mode is fixed at construction time so the business layer never
    branches on testnet vs mainnet.
    """

    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker: ...

    @abstractmethod
    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 300,
        end_time: int | None = None,
    ) -> list[Kline]: ...

    @abstractmethod
    def submit_order(self, request: OrderRequest) -> OrderResult: ...

    @abstractmethod
    def get_order(self, symbol: str, exchange_order_id: str) -> OrderResult: ...

    @abstractmethod
    def cancel_order(self, symbol: str, exchange_order_id: str) -> OrderResult: ...

    @abstractmethod
    def get_balance(self, asset: str) -> float: ...

    @property
    @abstractmethod
    def trading_mode(self) -> Literal["testnet", "mainnet"]: ...
```

Create `backend/tests/unit/execution/__init__.py` (empty file).

- [ ] **Step 13.4: Run, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_exchange_types.py
```

- [ ] **Step 13.5: Commit + push**

```bash
git add backend/src/execution/ \
        backend/tests/unit/execution/__init__.py \
        backend/tests/unit/execution/test_exchange_types.py
git commit -m "foundation(plan1): add ExchangeAdapter abstract interface + value types

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 14: RateLimiter (Token Bucket)

**Goal:** Binance REST weight limit is 1200/min (spec §6.2). A token bucket `acquire(tokens)` that blocks or raises if exceeded.

**Files:**
- Create: `backend/src/execution/exchange/rate_limiter.py`
- Create test: `backend/tests/unit/execution/test_rate_limiter.py`

### Steps

- [ ] **Step 14.1: Write failing test**

Create `backend/tests/unit/execution/test_rate_limiter.py`:

```python
from __future__ import annotations

import time

import pytest

from src.execution.exchange.rate_limiter import RateLimiter, RateLimitExceeded


def test_bucket_allows_up_to_capacity():
    limiter = RateLimiter(capacity=5, refill_per_second=0)  # no refill
    for _ in range(5):
        limiter.acquire(1, blocking=False)
    with pytest.raises(RateLimitExceeded):
        limiter.acquire(1, blocking=False)


def test_bucket_refills_over_time():
    limiter = RateLimiter(capacity=2, refill_per_second=10)  # refills very fast
    limiter.acquire(2, blocking=False)
    time.sleep(0.25)  # should refill ~2.5 tokens
    limiter.acquire(1, blocking=False)


def test_blocking_acquire_waits_until_refill():
    limiter = RateLimiter(capacity=1, refill_per_second=10)
    limiter.acquire(1, blocking=False)
    start = time.monotonic()
    limiter.acquire(1, blocking=True)
    elapsed = time.monotonic() - start
    assert 0.05 <= elapsed <= 0.5, f"expected ~0.1s wait, got {elapsed:.3f}"


def test_acquire_raises_if_request_exceeds_capacity():
    limiter = RateLimiter(capacity=5, refill_per_second=1)
    with pytest.raises(ValueError):
        limiter.acquire(10, blocking=False)
```

- [ ] **Step 14.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_rate_limiter.py
```

- [ ] **Step 14.3: Implement**

Create `backend/src/execution/exchange/rate_limiter.py`:

```python
"""Token bucket rate limiter. Thread-safe via a Lock.

Binance REST: weight limit is 1200 per minute → capacity=1200, refill=20/s.
Binance also has a 10s-level cap (~300 weight) — not modeled here; use a
second RateLimiter stacked in front if you need it.
"""
from __future__ import annotations

import threading
import time


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    def __init__(self, capacity: int, refill_per_second: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_per_second < 0:
            raise ValueError("refill_per_second must be non-negative")
        self._capacity = capacity
        self._refill = refill_per_second
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill_tokens_locked(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill)
        self._last = now

    def acquire(self, tokens: int = 1, *, blocking: bool = True, timeout: float | None = None) -> None:
        if tokens > self._capacity:
            raise ValueError(f"request {tokens} exceeds capacity {self._capacity}")
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill_tokens_locked()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                if not blocking:
                    raise RateLimitExceeded(
                        f"need {tokens} tokens, have {self._tokens:.2f}"
                    )
                need = tokens - self._tokens
                wait_s = need / self._refill if self._refill > 0 else 0.05
            if deadline is not None and time.monotonic() + wait_s > deadline:
                raise RateLimitExceeded("timeout waiting for tokens")
            time.sleep(min(wait_s, 0.1))
```

- [ ] **Step 14.4: Run, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_rate_limiter.py
```

- [ ] **Step 14.5: Commit + push**

```bash
git add backend/src/execution/exchange/rate_limiter.py \
        backend/tests/unit/execution/test_rate_limiter.py
git commit -m "foundation(plan1): add token-bucket RateLimiter for exchange calls

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 15: Retry/Backoff Decorator

**Goal:** Exponential backoff helper for transient exchange errors (network, 5xx). `@with_retry(retries=3, base_delay=0.5, max_delay=8.0)` style. Non-retriable errors (4xx except 429) pass through immediately.

**Files:**
- Create: `backend/src/execution/exchange/retry.py`
- Create test: `backend/tests/unit/execution/test_retry.py`

### Steps

- [ ] **Step 15.1: Write failing test**

Create `backend/tests/unit/execution/test_retry.py`:

```python
from __future__ import annotations

import pytest

from src.execution.exchange.retry import (
    ExchangeTemporarilyUnavailable, PermanentExchangeError, with_retry,
)


def test_succeeds_on_first_try_without_retry_overhead():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.01)
    def ok():
        calls["n"] += 1
        return "good"

    assert ok() == "good"
    assert calls["n"] == 1


def test_retries_on_transient_then_succeeds():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.01)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ExchangeTemporarilyUnavailable("transient")
        return "good"

    assert flaky() == "good"
    assert calls["n"] == 3


def test_permanent_error_is_not_retried():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.01)
    def broken():
        calls["n"] += 1
        raise PermanentExchangeError("4xx")

    with pytest.raises(PermanentExchangeError):
        broken()
    assert calls["n"] == 1


def test_gives_up_after_max_retries():
    calls = {"n": 0}

    @with_retry(retries=2, base_delay=0.01)
    def always_fails():
        calls["n"] += 1
        raise ExchangeTemporarilyUnavailable("down")

    with pytest.raises(ExchangeTemporarilyUnavailable):
        always_fails()
    assert calls["n"] == 3  # initial + 2 retries
```

- [ ] **Step 15.2: Run, verify fail**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_retry.py
```

- [ ] **Step 15.3: Implement**

Create `backend/src/execution/exchange/retry.py`:

```python
"""Retry decorator for exchange calls. Exponential backoff with jitter.

Two custom exception classes draw the retriable / non-retriable boundary:

- ExchangeTemporarilyUnavailable: 5xx, 429, timeout, connection error
- PermanentExchangeError: 4xx (except 429), malformed request

Callers raise the appropriate one; `with_retry` only retries the transient one.
"""
from __future__ import annotations

import functools
import logging
import random
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ExchangeTemporarilyUnavailable(Exception):
    """Retriable — caller will retry with backoff."""


class PermanentExchangeError(Exception):
    """Non-retriable — caller must fix the request."""


def with_retry(
    *,
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    jitter: float = 0.2,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except PermanentExchangeError:
                    raise
                except ExchangeTemporarilyUnavailable:
                    if attempt >= retries:
                        logger.warning("giving up on %s after %d attempts", fn.__name__, attempt + 1)
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    delay += random.uniform(0, delay * jitter)
                    logger.info("retry %s attempt %d after %.2fs", fn.__name__, attempt + 1, delay)
                    time.sleep(delay)
                    attempt += 1
        return wrapper
    return decorator
```

- [ ] **Step 15.4: Run, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_retry.py
```

- [ ] **Step 15.5: Commit + push**

```bash
git add backend/src/execution/exchange/retry.py \
        backend/tests/unit/execution/test_retry.py
git commit -m "foundation(plan1): add with_retry decorator + exchange error hierarchy

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 16: Binance Adapter Implementation

**Goal:** Concrete `BinanceAdapter(ExchangeAdapter)` wrapping `python-binance`. Maps Binance errors to the retry hierarchy; applies the RateLimiter before every REST call.

**Files:**
- Create: `backend/src/execution/exchange/binance_adapter.py`
- Create test: `backend/tests/unit/execution/test_binance_adapter_mock.py`
- Create test: `backend/tests/integration/test_binance_adapter.py`

### Steps

- [ ] **Step 16.1: Write failing unit test (HTTP mocked)**

Create `backend/tests/unit/execution/test_binance_adapter_mock.py`:

```python
"""Binance adapter with python-binance client mocked; verifies mapping logic."""
from __future__ import annotations

from unittest.mock import MagicMock

from binance.exceptions import BinanceAPIException

import pytest

from src.execution.exchange.binance_adapter import BinanceAdapter
from src.execution.exchange.retry import (
    ExchangeTemporarilyUnavailable, PermanentExchangeError,
)
from src.execution.exchange.types import OrderRequest


def _mk_binance_exception(status_code: int) -> BinanceAPIException:
    """Construct BinanceAPIException without going through its parser.

    The __init__ tries to JSON-parse the text; we bypass by using __new__
    and setting only the fields our adapter touches. Avoids brittleness
    across python-binance versions.
    """
    exc = BinanceAPIException.__new__(BinanceAPIException)
    exc.status_code = status_code
    exc.code = 0
    exc.message = f"mock {status_code}"
    exc.response = MagicMock()
    exc.args = (f"{status_code} mock error",)
    return exc


def _adapter_with_mock_client(mock_client):
    return BinanceAdapter(
        api_key="k", api_secret="s", trading_mode="testnet",
        _client_override=mock_client,
    )


def test_get_ticker_parses_price():
    mc = MagicMock()
    mc.get_symbol_ticker.return_value = {"symbol": "BTCUSDT", "price": "105.5"}
    a = _adapter_with_mock_client(mc)
    t = a.get_ticker("BTCUSDT")
    assert t.price == 105.5


def test_submit_order_returns_order_result():
    mc = MagicMock()
    mc.create_order.return_value = {
        "orderId": 12345,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "FILLED",
        "origQty": "0.01",
        "executedQty": "0.01",
        "cummulativeQuoteQty": "1055",
        "clientOrderId": "trace123",
    }
    a = _adapter_with_mock_client(mc)
    res = a.submit_order(OrderRequest(
        symbol="BTCUSDT", side="BUY", order_type="MARKET",
        quantity=0.01, client_order_id="trace123",
    ))
    assert res.exchange_order_id == "12345"
    assert res.status == "FILLED"
    assert res.avg_fill_price == 1055 / 0.01


def test_5xx_maps_to_transient():
    mc = MagicMock()
    mc.get_symbol_ticker.side_effect = _mk_binance_exception(500)
    a = _adapter_with_mock_client(mc)
    with pytest.raises(ExchangeTemporarilyUnavailable):
        a.get_ticker("BTCUSDT")


def test_4xx_maps_to_permanent():
    mc = MagicMock()
    mc.get_symbol_ticker.side_effect = _mk_binance_exception(400)
    a = _adapter_with_mock_client(mc)
    with pytest.raises(PermanentExchangeError):
        a.get_ticker("BTCUSDT")


def test_429_maps_to_transient():
    mc = MagicMock()
    mc.get_symbol_ticker.side_effect = _mk_binance_exception(429)
    a = _adapter_with_mock_client(mc)
    with pytest.raises(ExchangeTemporarilyUnavailable):
        a.get_ticker("BTCUSDT")
```

- [ ] **Step 16.2: Write failing integration test against Binance Testnet**

Create `backend/tests/integration/test_binance_adapter.py`:

```python
"""Live integration test — requires Binance Testnet API key in env.

Skipped if BINANCE_API_KEY not set to a non-placeholder value.
"""
from __future__ import annotations

import os

import pytest

from src.execution.exchange.binance_adapter import BinanceAdapter


def _skip_if_no_credentials():
    key = os.environ.get("BINANCE_API_KEY", "")
    secret = os.environ.get("BINANCE_API_SECRET", "")
    if not key or key.startswith("test-") or not secret or secret.startswith("test-"):
        pytest.skip("no real Binance testnet credentials in env")


def test_live_get_ticker():
    _skip_if_no_credentials()
    a = BinanceAdapter(
        api_key=os.environ["BINANCE_API_KEY"],
        api_secret=os.environ["BINANCE_API_SECRET"],
        trading_mode="testnet",
    )
    t = a.get_ticker("BTCUSDT")
    assert t.symbol == "BTCUSDT"
    assert t.price > 0


def test_live_get_klines():
    _skip_if_no_credentials()
    a = BinanceAdapter(
        api_key=os.environ["BINANCE_API_KEY"],
        api_secret=os.environ["BINANCE_API_SECRET"],
        trading_mode="testnet",
    )
    ks = a.get_klines("BTCUSDT", "1h", limit=5)
    assert len(ks) == 5
    for k in ks:
        assert k.close > 0
```

- [ ] **Step 16.3: Run, verify failure**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_binance_adapter_mock.py
```

- [ ] **Step 16.4: Implement BinanceAdapter**

Create `backend/src/execution/exchange/binance_adapter.py`:

```python
"""Binance REST adapter on top of python-binance.

testnet/mainnet selection via constructor; the business layer never sees the
distinction.

Every REST call passes through:
  1. RateLimiter.acquire (token bucket, Binance weight 1200/min)
  2. @with_retry decorator (exponential backoff for 5xx/429/timeout)

BinanceAPIException is mapped to our error hierarchy:
  - status 5xx or 429 or -1003 (too many requests) → ExchangeTemporarilyUnavailable
  - other 4xx → PermanentExchangeError
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.rate_limiter import RateLimiter
from src.execution.exchange.retry import (
    ExchangeTemporarilyUnavailable, PermanentExchangeError, with_retry,
)
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker

# Binance timeframe → candle duration
_TIMEFRAME_MAP = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
}


def _map_binance_error(exc: Exception) -> Exception:
    if isinstance(exc, BinanceRequestException):
        return ExchangeTemporarilyUnavailable(str(exc))
    if isinstance(exc, BinanceAPIException):
        status = getattr(exc, "status_code", 0) or 0
        if status >= 500 or status == 429:
            return ExchangeTemporarilyUnavailable(f"{status}: {exc}")
        return PermanentExchangeError(f"{status}: {exc}")
    return exc


class BinanceAdapter(ExchangeAdapter):
    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        trading_mode: Literal["testnet", "mainnet"],
        _client_override=None,  # test hook
    ):
        self._trading_mode = trading_mode
        testnet = trading_mode == "testnet"
        self._client = _client_override or Client(api_key, api_secret, testnet=testnet)
        # Binance weight limit: 1200/min → refill 20/s.
        self._limiter = RateLimiter(capacity=1200, refill_per_second=20)

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return self._trading_mode

    # -----------------------------------------------------------------
    # Market data
    # -----------------------------------------------------------------

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_ticker(self, symbol: str) -> Ticker:
        self._limiter.acquire(1)
        try:
            raw = self._client.get_symbol_ticker(symbol=symbol)
        except Exception as e:
            raise _map_binance_error(e) from e
        return Ticker(
            symbol=raw["symbol"],
            price=float(raw["price"]),
            fetched_at=datetime.now(timezone.utc),
        )

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 300,
        end_time: int | None = None,
    ) -> list[Kline]:
        interval = _TIMEFRAME_MAP[timeframe]
        # Weight varies by limit; use 5 as a safe default.
        self._limiter.acquire(5)
        try:
            raw = self._client.get_klines(symbol=symbol, interval=interval, limit=limit, endTime=end_time)
        except Exception as e:
            raise _map_binance_error(e) from e

        klines: list[Kline] = []
        for row in raw:
            klines.append(
                Kline(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
        return klines

    # -----------------------------------------------------------------
    # Orders
    # -----------------------------------------------------------------

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def submit_order(self, request: OrderRequest) -> OrderResult:
        self._limiter.acquire(1)
        kwargs = {
            "symbol": request.symbol,
            "side": request.side,
            "type": request.order_type,
            "quantity": request.quantity,
        }
        if request.order_type == "LIMIT":
            kwargs["timeInForce"] = "GTC"
            kwargs["price"] = request.price
        if request.client_order_id:
            kwargs["newClientOrderId"] = request.client_order_id
        try:
            raw = self._client.create_order(**kwargs)
        except Exception as e:
            raise _map_binance_error(e) from e
        return self._parse_order(raw)

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_order(self, symbol: str, exchange_order_id: str) -> OrderResult:
        self._limiter.acquire(1)
        try:
            raw = self._client.get_order(symbol=symbol, orderId=int(exchange_order_id))
        except Exception as e:
            raise _map_binance_error(e) from e
        return self._parse_order(raw)

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def cancel_order(self, symbol: str, exchange_order_id: str) -> OrderResult:
        self._limiter.acquire(1)
        try:
            raw = self._client.cancel_order(symbol=symbol, orderId=int(exchange_order_id))
        except Exception as e:
            raise _map_binance_error(e) from e
        return self._parse_order(raw)

    # -----------------------------------------------------------------
    # Account
    # -----------------------------------------------------------------

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_balance(self, asset: str) -> float:
        self._limiter.acquire(10)  # account endpoint is weight 10
        try:
            raw = self._client.get_asset_balance(asset=asset)
        except Exception as e:
            raise _map_binance_error(e) from e
        if not raw:
            return 0.0
        return float(raw.get("free", 0.0))

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _parse_order(raw: dict) -> OrderResult:
        filled = float(raw.get("executedQty", 0) or 0)
        quote = float(raw.get("cummulativeQuoteQty", 0) or 0)
        avg_price = quote / filled if filled > 0 and quote > 0 else None
        status = raw.get("status", "NEW")
        if status == "CANCELED":
            status = "CANCELED"
        return OrderResult(
            exchange_order_id=str(raw["orderId"]),
            symbol=raw["symbol"],
            side=raw["side"],
            order_type=raw["type"],
            status=status,
            requested_quantity=float(raw.get("origQty", 0) or 0),
            filled_quantity=filled,
            avg_fill_price=avg_price,
            client_order_id=raw.get("clientOrderId"),
        )
```

- [ ] **Step 16.5: Run mock tests, expect PASS**

```bash
cd backend && .venv/bin/pytest -q tests/unit/execution/test_binance_adapter_mock.py
```

Integration test is automatically skipped if no real credentials are in env.

- [ ] **Step 16.6: Commit + push**

```bash
git add backend/src/execution/exchange/binance_adapter.py \
        backend/tests/unit/execution/test_binance_adapter_mock.py \
        backend/tests/integration/test_binance_adapter.py
git commit -m "foundation(plan1): add BinanceAdapter with rate limiting + retry-aware error mapping

Testnet/mainnet selection via constructor; business code never branches on
trading_mode. All REST calls pass through the token-bucket limiter and the
retry decorator. Binance errors mapped to ExchangeTemporarilyUnavailable
vs PermanentExchangeError per status code.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

---

## Task 17: End-to-End Foundation Smoke Test

**Goal:** A single integration test that exercises the full foundation stack: migrations apply cleanly, event can go from business write → Outbox → Shuttle → Redis Streams → consumer with Inbox idempotency → ack. This locks in the foundation contracts for subsequent plans.

**Files:**
- Create: `backend/tests/integration/test_foundation_smoke.py`

### Steps

- [ ] **Step 17.1: Write the smoke test**

Create `backend/tests/integration/test_foundation_smoke.py`:

```python
"""Smoke test: full foundation stack in one scenario.

  1. PostgresContainer up → run all migrations
  2. RedisContainer up
  3. Insert a Position and record a PositionOpened event via OutboxWriter (same txn)
  4. Run EventShuttle.drain_once → row marked published_at
  5. Consume from Redis Streams via RedisStreamsBus
  6. InboxGuard.claim succeeds once, blocks second attempt
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from alembic import command
from alembic.config import Config

from src.events.bus import RedisStreamsBus
from src.events.contracts import PositionOpened
from src.events.inbox import InboxGuard
from src.events.outbox import OutboxWriter
from src.shared.models import Position
from src.workers.event_shuttle import EventShuttle


@pytest.fixture(scope="module")
def pg_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        cfg = Config(os.path.join(os.path.dirname(__file__), "../../alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")
        yield url


@pytest.fixture(scope="module")
def redis_url():
    with RedisContainer("redis:7-alpine") as rc:
        yield rc.get_connection_url()


def test_full_foundation_stack(pg_url, redis_url):
    engine = create_engine(pg_url)
    bus = RedisStreamsBus(redis_url)
    stream = "position.opened"
    bus.ensure_group(stream, "smoke-consumer")

    writer = OutboxWriter()

    # 1+2: Write position AND outbox row in the same txn
    with Session(engine) as s:
        pos = Position(
            trading_mode="testnet",
            account_id=1,
            symbol="BTCUSDT",
            quantity=0.01,
            entry_price=100,
            stop_loss=95,
            opened_at=datetime.now(timezone.utc),
        )
        s.add(pos)
        s.flush()

        evt = PositionOpened(
            position_id=pos.id, symbol=pos.symbol,
            quantity=float(pos.quantity),
            entry_price=float(pos.entry_price),
            stop_loss=float(pos.stop_loss),
        )
        writer.record(
            s,
            aggregate_type="position",
            aggregate_id=pos.id,
            event=evt,
            account_id=1,
            trading_mode="testnet",
            trace_id="smoke-trace-1",
        )
        s.commit()

    # 3: Shuttle drains
    shuttle = EventShuttle(engine=engine, bus=bus, stream_for_event=lambda e: e)
    published = shuttle.drain_once()
    assert published == 1

    # 4: Consume from Streams
    messages = list(bus.consume(stream, "smoke-consumer", "c1", count=5, block_ms=500))
    assert len(messages) == 1
    msg_id, envelope = messages[0]
    assert envelope.event_type == "position.opened"
    assert envelope.payload["symbol"] == "BTCUSDT"

    # 5: InboxGuard idempotency
    guard = InboxGuard(consumer_name="smoke-consumer")
    with Session(engine) as s:
        assert guard.claim(s, envelope.event_id) is True
        s.commit()
    with Session(engine) as s:
        assert guard.claim(s, envelope.event_id) is False  # duplicate blocked

    bus.ack(stream, "smoke-consumer", msg_id)
```

- [ ] **Step 17.2: Run the smoke test**

```bash
cd backend && .venv/bin/pytest -q tests/integration/test_foundation_smoke.py -v
```

Expected: PASS. First run is slow (~30s) due to container startup; subsequent runs faster.

- [ ] **Step 17.3: Run the full test suite to confirm nothing else broke**

```bash
cd backend && .venv/bin/pytest -q
```

Expected: All tests pass (existing suite + everything added in this plan).

- [ ] **Step 17.4: Commit + push**

```bash
git add backend/tests/integration/test_foundation_smoke.py
git commit -m "foundation(plan1): add end-to-end smoke test for foundation stack

Exercises: migrations apply → business write + Outbox in same txn → shuttle
publishes → Streams consume → Inbox idempotency → ack. This is the
foundation contract; subsequent plans build on these primitives.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

- [ ] **Step 17.5: Deploy to dev server per CLAUDE.md rule**

```bash
cd E:/ai/alpha-pilot && bash scripts/deploy-dev.sh
```

If deploy script fails, capture the output and address in a follow-up commit; do not proceed to Plan 2 until dev is stable on this commit.

---

## Self-Review Checklist (run after executing the plan, before marking complete)

- [ ] All 17 tasks committed, each with passing tests.
- [ ] `alembic history` shows unbroken chain `20260317_0004 → 20260421_0001 → ... → 20260421_0007`.
- [ ] `cd backend && .venv/bin/pytest -q` green (no regressions).
- [ ] `default account id=1` exists and `risk_profile id=1` exists after migrations.
- [ ] `event_outbox` and `event_inbox` tables exist with expected indexes (`ix_event_outbox_unpublished`, `ix_event_inbox_consumer_name_event_id`).
- [ ] `ExchangeAdapter.__init__.py` does not expose any Binance-specific types.
- [ ] `RateLimiter` + `with_retry` have no shared state between instances (thread-safe).
- [ ] All commits have the required `Co-Authored-By` footer.
- [ ] Dev server successfully deployed on the final commit.

---

## What This Plan Does NOT Build

- No business logic (Factor computation, Regime classifier, AIT Pipeline, Guard rules — all in Plan 2)
- No REST routers or WebSocket (Plan 3)
- No frontend changes (Plan 4)
- No LLM adapter (Plan 2)
- No actual order placement workflow wiring (Plan 2 consumes this plan's adapter)

The foundation is complete when Plan 2 can `from src.execution.exchange.binance_adapter import BinanceAdapter` and `from src.events.outbox import OutboxWriter` without modifying either.
