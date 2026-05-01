"""CRUD for src.models.task_request."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.task_request import TaskRequest


class TaskRequestCrud(BaseCrud[TaskRequest]):
    model = TaskRequest

    def create_pending(
        self,
        session: Session,
        *,
        task_type: str,
        payload: dict,
        trading_mode: str = "testnet",
    ) -> TaskRequest:
        obj = TaskRequest(
            task_type=task_type,
            payload=payload or {},
            status="PENDING",
            attempts=0,
            trading_mode=trading_mode,
        )
        session.add(obj)
        session.flush()
        return obj

    def mark_running(self, session: Session, task_id: int) -> TaskRequest | None:
        """CAS 风格: 仅当 status=PENDING 时切到 RUNNING; 失败返 None。"""
        now = datetime.now(timezone.utc)
        result = session.execute(
            update(TaskRequest)
            .where(TaskRequest.id == task_id, TaskRequest.status == "PENDING")
            .values(status="RUNNING", started_at=now, attempts=TaskRequest.attempts + 1)
        )
        session.flush()
        if result.rowcount == 0:
            return None
        return session.get(TaskRequest, task_id)

    def mark_success(self, session: Session, task_id: int) -> TaskRequest:
        obj = self.get(session, task_id)
        obj.status = "SUCCESS"
        obj.finished_at = datetime.now(timezone.utc)
        obj.error_message = None
        session.flush()
        return obj

    def mark_failed(self, session: Session, task_id: int, error_message: str) -> TaskRequest:
        obj = self.get(session, task_id)
        obj.status = "FAILED"
        obj.finished_at = datetime.now(timezone.utc)
        obj.error_message = error_message
        session.flush()
        return obj

    def find_orphan_running(self, session: Session, threshold_seconds: int = 300) -> list[TaskRequest]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold_seconds)
        return list(
            session.execute(
                select(TaskRequest).where(
                    TaskRequest.status == "RUNNING",
                    TaskRequest.started_at < cutoff,
                )
            ).scalars()
        )


task_request_crud = TaskRequestCrud()
