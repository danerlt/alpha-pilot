"""Verifies that all retrofitted models expose account_id with default=1."""
from __future__ import annotations

from src.shared.models import (
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

MULTI_TENANT_MODELS = [
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
    RiskProfile,
    ParameterVersion,
]


def test_every_business_model_has_account_id_column():
    for model in MULTI_TENANT_MODELS:
        assert "account_id" in model.__table__.columns, f"{model.__name__} missing account_id"


def test_account_id_default_is_one():
    for model in MULTI_TENANT_MODELS:
        col = model.__table__.columns["account_id"]
        assert col.default.arg == 1 or str(col.default.arg) == "1", (
            f"{model.__name__}.account_id default != 1"
        )


def test_account_model_has_no_account_id():
    assert "account_id" not in Account.__table__.columns, "Account must not self-reference"
