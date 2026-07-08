import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.common.enums import UserRole, UserStatus
from src.configs.app_configs import AppConfig as Settings
from src.models.base import Base
from src.models.user import User
from src.services.admin_bootstrap import ensure_default_admin
from src.services.auth import hash_password


def make_db():
    engine = create_engine(
        os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"),
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine, tables=[User.__table__])
    return engine, TestingSessionLocal()


def test_ensure_default_admin_creates_user():
    engine, db = make_db()
    try:
        settings = Settings(_env_file=None, DEFAULT_ADMIN_EMAIL="danerlt001@gmail.com", DEFAULT_ADMIN_USERNAME="danerlt001", DEFAULT_ADMIN_PASSWORD="Alpha123456@#$")
        changed = ensure_default_admin(db, settings)
        user = db.query(User).filter(User.email == "danerlt001@gmail.com").first()

        assert changed is True
        assert user is not None
        assert user.username == "danerlt001"
        assert user.role == UserRole.ADMIN.value
        assert user.status == UserStatus.ACTIVE.value
    finally:
        db.close()
        engine.dispose()


def test_ensure_default_admin_promotes_existing_user_and_resets_password():
    engine, db = make_db()
    try:
        old_hash = hash_password("old-pass-123")
        existing = User(
            username="legacy",
            email="danerlt001@gmail.com",
            password_hash=old_hash,
            role=UserRole.USER.value,
            status=UserStatus.DISABLED.value,
        )
        db.add(existing)
        db.commit()

        settings = Settings(_env_file=None, DEFAULT_ADMIN_EMAIL="danerlt001@gmail.com", DEFAULT_ADMIN_USERNAME="danerlt001", DEFAULT_ADMIN_PASSWORD="Alpha123456@#$")
        changed = ensure_default_admin(db, settings)
        user = db.query(User).filter(User.email == "danerlt001@gmail.com").first()

        assert changed is True
        assert user is not None
        assert user.username == "danerlt001"
        assert user.role == UserRole.ADMIN.value
        assert user.status == UserStatus.ACTIVE.value
        assert user.password_hash != old_hash
    finally:
        db.close()
        engine.dispose()


def test_ensure_default_risk_profile_creates_and_idempotent(pg_session):
    """决策链前置:缺 active risk_profile 则每轮 skipped 不交易。用真实 PG
    (RiskProfile 时间戳 server_default 在 sqlite 不兼容)。"""
    from src.models.account_entity import RiskProfile
    from src.services.admin_bootstrap import ensure_default_risk_profile

    settings = Settings(_env_file=None)
    assert ensure_default_risk_profile(pg_session, settings, account_id=1) is True
    prof = (
        pg_session.query(RiskProfile)
        .filter(RiskProfile.account_id == 1, RiskProfile.active.is_(True))
        .first()
    )
    assert prof is not None
    assert float(prof.max_daily_loss_pct) == 0.03
    assert prof.active is True
    # 幂等:已存在不重复建
    assert ensure_default_risk_profile(pg_session, settings, account_id=1) is False
    assert (
        pg_session.query(RiskProfile)
        .filter(RiskProfile.account_id == 1)
        .count()
        == 1
    )
