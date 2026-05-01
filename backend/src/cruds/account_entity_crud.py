"""CRUD for src.models.account_entity."""
from __future__ import annotations

from src.models.account_entity import Account, RiskProfile, ParameterVersion
from src.cruds.base_crud import BaseCrud


class AccountCrud(BaseCrud[Account]):
    model = Account

account_crud = AccountCrud()

class RiskProfileCrud(BaseCrud[RiskProfile]):
    model = RiskProfile

risk_profile_crud = RiskProfileCrud()

class ParameterVersionCrud(BaseCrud[ParameterVersion]):
    model = ParameterVersion

parameter_version_crud = ParameterVersionCrud()
