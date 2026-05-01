from sqlalchemy import BigInteger, Boolean, String, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, BigIntPk


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value_json: Mapped[dict | str | int | float | bool | None] = mapped_column(JSON)
    encrypted_value: Mapped[str | None] = mapped_column(Text)
    is_secret: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(String(255))
