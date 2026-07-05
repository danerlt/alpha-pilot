"""CRUD for src.models.account_entity."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.account_entity import Account, ParameterVersion, RiskProfile


class AccountCrud(BaseCrud[Account]):
    model = Account

account_crud = AccountCrud()

class RiskProfileCrud(BaseCrud[RiskProfile]):
    model = RiskProfile

    def find_active(self, session: Session, *, account_id: int = 1) -> RiskProfile | None:
        return session.execute(
            select(RiskProfile).where(
                RiskProfile.account_id == account_id,
                RiskProfile.active.is_(True),
            ).order_by(RiskProfile.version.desc()).limit(1)
        ).scalars().first()

risk_profile_crud = RiskProfileCrud()

class ParameterVersionCrud(BaseCrud[ParameterVersion]):
    model = ParameterVersion

parameter_version_crud = ParameterVersionCrud()
