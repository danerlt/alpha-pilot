"""BaseCrud[ModelT] — 标准 CRUD + 实体专属方法命名约定。

约定（spec v3.7 §4.3）：
- ``add(session, **kwargs)`` 创建
- ``get(session, id)`` 不存在抛 ``DBException(NOT_FOUND)``
- ``get_or_none(session, id)`` 不存在返 None
- ``find_by_xxx(session, ...)`` 按条件查询，返列表
- ``update(session, id, **kwargs)``
- ``delete(session, id)`` 软删（要求 model 含 delete_flag）
- ``hard_delete(session, id)``
- 状态变更动词：``mark_<status>(session, id, ...)``
- 批量状态：``bulk_mark_<status>(session, status_in=[...])``
- 累计计数：``bump_failed_attempts(session, id, error: str)``
- 进度更新：``update_progress(session, id, progress: int)``

强制规范：
- crud 方法**不 commit**（commit 由 service 显式调用）
- service 层只调 ``xxx_crud.method()``，不写 ``session.query(Model)``
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.exception.errors import DBException
from src.common.response.response_code import ErrorCode
from src.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseCrud(Generic[ModelT]):
    """所有实体 crud 的基类。子类只需 ``model = SomeModel``。"""

    model: type[ModelT]

    # ── 增 ─────────────────────────────────────────────────────────────
    def add(self, session: Session, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        session.add(obj)
        session.flush()
        return obj

    def bulk_add(self, session: Session, items: list[dict[str, Any]]) -> list[ModelT]:
        objs = [self.model(**item) for item in items]
        session.add_all(objs)
        session.flush()
        return objs

    # ── 查 ─────────────────────────────────────────────────────────────
    def get(self, session: Session, id: int) -> ModelT:
        """按主键查询；不存在抛 DBException(NOT_FOUND)。"""
        obj = session.get(self.model, id)
        if obj is None:
            raise DBException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"{self.model.__name__} id={id} not found",
            )
        return obj

    def get_or_none(self, session: Session, id: int) -> ModelT | None:
        return session.get(self.model, id)

    def list_all(self, session: Session) -> list[ModelT]:
        """查全表。仅小表用；大表请用分页方法。"""
        return list(session.execute(select(self.model)).scalars())

    def find_by_status(self, session: Session, statuses: list[str]) -> list[ModelT]:
        """按 status in (...) 查询。要求 model 有 status 列。"""
        if not hasattr(self.model, "status"):
            raise NotImplementedError(f"{self.model.__name__} has no 'status' column")
        return list(
            session.execute(
                select(self.model).where(self.model.status.in_(statuses))
            ).scalars()
        )

    # ── 改 ─────────────────────────────────────────────────────────────
    def update(self, session: Session, id: int, **kwargs: Any) -> ModelT:
        obj = self.get(session, id)
        for k, v in kwargs.items():
            setattr(obj, k, v)
        session.flush()
        return obj

    # ── 删 ─────────────────────────────────────────────────────────────
    def delete(self, session: Session, id: int) -> None:
        """软删（要求 model 有 delete_flag）。"""
        obj = self.get(session, id)
        if hasattr(obj, "delete_flag"):
            obj.delete_flag = True
            session.flush()
        else:
            session.delete(obj)
            session.flush()

    def hard_delete(self, session: Session, id: int) -> None:
        obj = self.get(session, id)
        session.delete(obj)
        session.flush()
