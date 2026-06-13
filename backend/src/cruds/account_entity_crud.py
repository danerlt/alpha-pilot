"""CRUD for src.models.account_entity."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.account_entity import Account, ParameterVersion, RiskProfile


class AccountCrud(BaseCrud[Account]):
    model = Account

account_crud = AccountCrud()

class RiskProfileCrud(BaseCrud[RiskProfile]):
    model = RiskProfile

risk_profile_crud = RiskProfileCrud()

class ParameterVersionCrud(BaseCrud[ParameterVersion]):
    model = ParameterVersion

parameter_version_crud = ParameterVersionCrud()
