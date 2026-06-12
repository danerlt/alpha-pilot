"""Commands router — 手动操作 / KillSwitch 端点 (Plan 3 Part B)。

  POST /api/commands/close-position/{position_id}
  POST /api/commands/close-all              (body: {confirmation: "CLOSE ALL", reason})
                                            → 异步入队, 返回 {task_id, status: "queued"},
                                              结果查 GET /api/tasks/{task_id} (spec §4.9.1)
  POST /api/commands/resolve-breaker/{event_id}
  POST /api/commands/pause                  (body: {reason})
  POST /api/commands/resume                 (body: {reason})
  GET  /api/commands/kill-switch            → 当前 active/paused

危险操作要求 body.confirmation 字段防误触; 全部走 ManualOpsService /
KillSwitchService, 自动写 audit_logs + manual.override 事件。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.exception.errors import DBException, ParamsException
from src.common.response.response_code import ErrorCode
from src.controllers.dependencies import get_adapter, require_admin
from src.schemas.command import (
    CloseAllCreate,
    ClosePositionCreate,
    PauseCreate,
    ResolveBreakerCreate,
)
from src.services.risk.kill_switch import KillSwitchService
from src.services.manual_ops import ManualOpsService
from src.services.events.outbox import OutboxWriter
from src.services.task_dispatcher import get_task_dispatcher
from src.db.session import get_db

router = APIRouter(prefix="/api/commands", tags=["commands"])


# 旧名 _adapter 保留为别名 — 测试通过 monkeypatch src.controllers.api.v1.risk.commands._adapter
# 的方式注入 mock; 见 backend/tests/api/test_commands.py
_adapter = get_adapter


# ----- Endpoints ------------------------------------------------------------
# 所有写操作要求 admin (require_admin), 防止未授权调用. (Critical fix C1)


@router.post("/close-position/{position_id}")
@api_response()
def close_position(
    position_id: int,
    body: ClosePositionCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    svc = ManualOpsService(db, _adapter(), outbox=OutboxWriter())
    trade = svc.manual_close_position(
        position_id=position_id, reason=body.reason,
        operator_user_id=current_admin.id,
    )
    db.commit()
    if trade is None:
        raise DBException(error_code=ErrorCode.NOT_FOUND, message="position not open or not found")
    return {"position_id": position_id, "trade_id": trade.id, "status": "closed"}


@router.post("/close-all")
@api_response()
def close_all(
    body: CloseAllCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """一键全平 — HTTP 触发的耗时业务, 走 task_requests 异步入队 (project.md §8)。

    立即返回 task_id; 执行结果通过 GET /api/tasks/{task_id} 查询,
    或订阅 WS 的 task.status_changed 事件。
    """
    if body.confirmation != "CLOSE ALL":
        raise ParamsException("must confirm with 'CLOSE ALL'")
    task_id = get_task_dispatcher().enqueue(
        "MANUAL_CLOSE_ALL",
        {
            "account_id": body.account_id,
            "trading_mode": body.trading_mode,
            "reason": body.reason,
            "operator_user_id": current_admin.id,
        },
        trading_mode=body.trading_mode,
    )
    return {"task_id": task_id, "status": "queued"}


@router.post("/resolve-breaker/{event_id}")
@api_response()
def resolve_breaker(
    event_id: int,
    body: ResolveBreakerCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    svc = ManualOpsService(db, _adapter(), outbox=OutboxWriter())
    ok = svc.manual_resolve_circuit_breaker(
        risk_event_id=event_id, reason=body.reason,
        operator_user_id=current_admin.id,
    )
    db.commit()
    if not ok:
        raise DBException(error_code=ErrorCode.NOT_FOUND, message="risk_event not found")
    return {"risk_event_id": event_id, "resolved": True}


@router.post("/pause")
@api_response()
def pause(
    body: PauseCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    svc = KillSwitchService(db)
    svc.pause(operator_user_id=current_admin.id, reason=body.reason)
    db.commit()
    return {"state": "paused"}


@router.post("/resume")
@api_response()
def resume(
    body: PauseCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    svc = KillSwitchService(db)
    svc.resume(operator_user_id=current_admin.id, reason=body.reason)
    db.commit()
    return {"state": "active"}


@router.get("/kill-switch")
@api_response()
def kill_switch_state(
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    return {"state": KillSwitchService(db).state()}
