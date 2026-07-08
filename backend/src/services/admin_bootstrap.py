from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from src.common.enums import UserRole, UserStatus
from src.configs.app_configs import AppConfig as Settings
from src.models.user import User
from src.services.auth import hash_password, verify_password

logger = logging.getLogger(__name__)


def _derive_username(settings: Settings) -> str:
    if settings.DEFAULT_ADMIN_USERNAME.strip():
        return settings.DEFAULT_ADMIN_USERNAME.strip()
    email = settings.DEFAULT_ADMIN_EMAIL.strip().lower()
    return (email.split('@')[0] if '@' in email else email)[:50] or 'admin'


def ensure_default_admin(db: Session, settings: Settings) -> bool:
    email = settings.DEFAULT_ADMIN_EMAIL.strip().lower()
    password = settings.DEFAULT_ADMIN_PASSWORD
    if not email or not password:
        return False

    username = _derive_username(settings)
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
        )
        db.add(user)
        db.commit()
        logger.info("Bootstrapped default admin user: %s", email)
        return True

    changed = False
    if user.role != UserRole.ADMIN.value:
        user.role = UserRole.ADMIN.value
        changed = True
    if user.status != UserStatus.ACTIVE.value:
        user.status = UserStatus.ACTIVE.value
        changed = True
    if user.username != username:
        user.username = username
        changed = True
    if not verify_password(password, user.password_hash):
        user.password_hash = hash_password(password)
        changed = True

    if changed:
        db.commit()
        logger.info("Ensured default admin user is active/admin and password-synced: %s", email)

    return changed


def ensure_default_risk_profile(
    db: Session, settings: Settings, account_id: int = 1,
) -> bool:
    """开箱确保 account_id 有 active risk_profile。

    策略调度链 (new_strategy_pipeline_job) 每轮先 _load_active_risk_profile,
    找不到就整轮 skipped —— 没有它,配好 Key 也永远不会自动决策/下单。
    生产代码此前无任何创建入口 (只有测试在建),导致新部署开箱决策链不跑。
    这里用 env 硬风控参数创建 version=1 active profile (前端后续可改)。
    """
    from src.models.account_entity import RiskProfile

    existing = (
        db.query(RiskProfile)
        .filter(RiskProfile.account_id == account_id, RiskProfile.active.is_(True))
        .first()
    )
    if existing is not None:
        return False

    profile = RiskProfile(
        account_id=account_id,
        name="default",
        max_position_size_pct=getattr(settings, "MAX_POSITION_SIZE_PCT", 0.20),
        max_daily_loss_pct=getattr(settings, "MAX_DAILY_LOSS_PCT", 0.03),
        max_consecutive_losses=getattr(settings, "MAX_CONSECUTIVE_LOSSES", 3),
        max_single_risk_pct=getattr(settings, "MAX_SINGLE_RISK_PCT", 0.01),
        version=1,
        active=True,
    )
    db.add(profile)
    db.commit()
    logger.info("Bootstrapped default active risk_profile for account_id=%s", account_id)
    return True
