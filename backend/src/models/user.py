from sqlalchemy import BigInteger, Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.common.enums import UserRole, UserStatus
from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER.value)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=UserStatus.ACTIVE.value)
    last_login_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    totp_secret: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="Fernet 加密的 TOTP secret")
    two_fa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
