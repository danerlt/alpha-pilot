from sqlalchemy import BigInteger, Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, BigIntPk


class SymbolConfig(Base):
    __tablename__ = "symbol_configs"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(nullable=False, default=1)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    base_asset: Mapped[str] = mapped_column(String(20), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(20), nullable=False, default="USDT")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default="15m")
    max_position_size_pct: Mapped[float | None] = mapped_column(Numeric(5, 4))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(Integer)
    updated_by: Mapped[int | None] = mapped_column(Integer)
