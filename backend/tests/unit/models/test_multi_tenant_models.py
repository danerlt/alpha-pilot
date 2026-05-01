"""Verifies multi-tenant models expose account_id per the documented contract.

Two classes of models:

- RETROFITTED_MODELS — existing V0.0/V0.1 business tables that were extended
  with account_id via migration 20260421_0001. These MUST have a Python-level
  default=1 so code written before the refactor (which doesn't pass account_id)
  keeps working against the default account.

- FRESHLY_ADDED_MODELS — new V0.1 tables (RiskProfile, ParameterVersion) where
  every insert is written in new code that already knows about the multi-tenant
  contract. These MUST NOT have a silent default — callers must pass account_id
  explicitly so "forgot to set tenant" surfaces as a programming error.
"""
from __future__ import annotations

from src.models import (
    Account,
    AccountSnapshot,
    AIDecision,
    AuditLog,
    Candle,
    DailyReport,
    ExperienceRecord,
    IndicatorSnapshot,
    Order,
    ParameterVersion,
    Position,
    RegimeSnapshot,
    RiskEvent,
    RiskProfile,
    SymbolConfig,
    Trade,
)

RETROFITTED_MODELS = [
    Position,
    Order,
    Trade,
    Candle,
    IndicatorSnapshot,
    RegimeSnapshot,
    AccountSnapshot,
    AIDecision,
    ExperienceRecord,
    RiskEvent,
    SymbolConfig,
    AuditLog,
    DailyReport,
]

FRESHLY_ADDED_MODELS = [
    RiskProfile,
    ParameterVersion,
]

ALL_MULTI_TENANT_MODELS = RETROFITTED_MODELS + FRESHLY_ADDED_MODELS


def test_every_business_model_has_account_id_column():
    for model in ALL_MULTI_TENANT_MODELS:
        assert "account_id" in model.__table__.columns, f"{model.__name__} missing account_id"


def test_every_business_model_account_id_is_not_null():
    for model in ALL_MULTI_TENANT_MODELS:
        col = model.__table__.columns["account_id"]
        assert col.nullable is False, f"{model.__name__}.account_id must be NOT NULL"


def test_retrofitted_models_default_to_one():
    for model in RETROFITTED_MODELS:
        col = model.__table__.columns["account_id"]
        assert col.default is not None, f"{model.__name__}.account_id missing default"
        assert col.default.arg == 1, (
            f"{model.__name__}.account_id default != 1 (got {col.default.arg!r})"
        )


def test_fresh_models_have_no_silent_default():
    for model in FRESHLY_ADDED_MODELS:
        col = model.__table__.columns["account_id"]
        assert col.default is None, (
            f"{model.__name__}.account_id must NOT have a Python default — "
            f"callers must pass account_id explicitly"
        )


def test_account_model_has_no_account_id():
    assert "account_id" not in Account.__table__.columns, "Account must not self-reference"
