from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from src.services.auth import hash_password, verify_password
from src.shared.config import Settings
from src.shared.enums import UserRole, UserStatus
from src.models.user import User

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
