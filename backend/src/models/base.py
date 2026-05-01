"""DB Model 基类与公共 Mixin。

约定（v3.7 + 老板补充）：
- ``Base`` **不含 ``id``** 字段（决策 2：每个 model 自定义 BigInteger autoincrement）
- ``Base`` **包含通用字段**（每个表都需要）：created_at / updated_at / enable_flag / delete_flag
- ``TradingModeMixin`` 按需继承（业务表需要 testnet/mainnet 隔离时继承）
- 不再使用 ``BigIntPk`` 类型别名（删 sqlite variant，统一用 BigInteger，测试改用真 PG）

**强制规则**：所有 Model 的 ``Mapped[...] = mapped_column(...)`` 字段定义**必须保持单行**，
便于 grep / IDE 跳转 / 字段速览。注释写在行尾或单独 ``#`` 注释行。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ── 临时兼容：sqlite in-memory 测试需要的 PK 类型 ─────────────────────────────
# 决策 3（B）说"删 sqlite variant"。但所有现有测试依赖 sqlite，一次性改 PG 工作量大。
# Stage 2 阶段：保留 BigIntPk 作为 model 主键类型（业务代码 grep 不到 BigIntPk）。
# Stage 2 末尾任务：把测试 fixture 全切 testcontainers PG，再删除本类型别名。
BigIntPk = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    """所有 ORM model 的基类。Base 含通用字段（每个表都有）+ 不含 id。"""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="记录创建时间（UTC）")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="记录最后更新时间（UTC）")
    enable_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("TRUE"), comment="是否有效（False=禁用，业务过滤用）")
    delete_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("FALSE"), comment="是否软删（True=已删除，物理保留）")


class TradingModeMixin:
    """需要按 testnet/mainnet 隔离的表显式继承。

    业务表（Position / Order / Trade / Decision / Indicator / Regime / ...）继承；
    全局表（User / SystemSetting / AuditLog / SymbolConfig）不继承。
    """

    trading_mode: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="testnet/mainnet 数据隔离")
