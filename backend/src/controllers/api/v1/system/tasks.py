"""Tasks router — 异步任务状态查询 (project.md §8 三层持久化的 HTTP 兜底层)。

  GET /api/tasks/{task_id}

任务由 admin-only 端点提交 (如 close-all), 查询同样要求 admin。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.exception.errors import DBException
from src.common.response.response_code import ErrorCode
from src.controllers.dependencies import require_admin
from src.cruds.task_request_crud import task_request_crud
from src.db.session import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}")
@api_response()
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    task = task_request_crud.get_or_none(db, task_id)
    if task is None:
        raise DBException(error_code=ErrorCode.NOT_FOUND, message="task not found")
    return {
        "id": task.id,
        "task_type": task.task_type,
        "status": task.status,
        "attempts": task.attempts,
        "enqueued_at": task.enqueued_at.isoformat() if task.enqueued_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        "error_message": task.error_message,
        "trading_mode": task.trading_mode,
    }
