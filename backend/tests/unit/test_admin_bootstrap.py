from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.services.admin_bootstrap import ensure_default_admin
from src.shared.config import Settings
from src.shared.enums import UserRole, UserStatus
from src.models.base import Base
from src.models.user import User
from src.services.auth import hash_password


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
