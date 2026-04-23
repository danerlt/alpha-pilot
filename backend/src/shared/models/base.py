from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# SQLite 的 AUTOINCREMENT 只对 INTEGER PRIMARY KEY 生效, 不支持 BIGINT。
# with_variant 让单元测试用 SQLite in-memory 时 fallback 到 INTEGER,
# 生产 Postgres 仍然得到 BIGINT。所有主键都用 BigIntPk, 避免各模型自行处理。
BigIntPk = BigInteger().with_variant(Integer(), "sqlite")


class TimestampMixin:
    """所有表的创建/更新时间基类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
