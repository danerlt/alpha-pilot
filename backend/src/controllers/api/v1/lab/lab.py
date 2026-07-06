"""Lab — /api/lab 策略实验室域 (handoff 3.5)。

权限 (P4 RBAC 矩阵): 查看=lab.view (全角色); 提交/启动/终止=lab.submit_candidate
(trader+); 批准灰度/上线=lab.approve_promote (admin+)。门槛校验在服务端。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.configs.app_configs import get_settings
from src.db.session import get_db
from src.schemas.lab_read import LabCandidateRead, LabHistoryItemRead
from src.services.events.outbox import OutboxWriter
from src.services.lab.lab_service import LabService
from src.services.system.permissions import require_permission

router = APIRouter(prefix="/api/lab", tags=["lab"])


class LabCandidateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    params: dict = Field(default_factory=dict)
    shadow_days_target: int = Field(default=14, ge=1, le=90)


class LabTerminateCreate(BaseModel):
    reason: str = Field(default="", max_length=500)


def _mode() -> str:
    mode = get_settings().TRADING_MODE
    return mode.value if hasattr(mode, "value") else mode


def _svc(db: Session) -> LabService:
    return LabService(db, outbox=OutboxWriter())


@router.get("/candidates", response_model=Response[list[LabCandidateRead]])
@api_response()
def list_candidates(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("lab.view")),
):
    """候选列表: stage/影子进度/影子 vs 线上对比/promote 门槛状态。"""
    return _svc(db).list_candidates(trading_mode=_mode())


@router.post("/candidates", response_model=Response[LabCandidateRead])
@api_response()
def submit_candidate(
    body: LabCandidateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("lab.submit_candidate")),
):
    """提交候选 (人工提案) → QUEUED。"""
    svc = _svc(db)
    row = svc.submit(
        name=body.name, description=body.description, params=body.params,
        trading_mode=_mode(), user_id=current_user.id,
        shadow_days_target=body.shadow_days_target,
    )
    return svc.candidate_detail(row)


@router.post("/candidates/{candidate_id}/start", response_model=Response[LabCandidateRead])
@api_response()
def start_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("lab.submit_candidate")),
):
    """开始影子运行: QUEUED → SHADOW。"""
    svc = _svc(db)
    row = svc.start_shadow(
        candidate_id=candidate_id, user_id=current_user.id, trading_mode=_mode(),
    )
    return svc.candidate_detail(row)


@router.post("/candidates/{candidate_id}/promote", response_model=Response[LabCandidateRead])
@api_response()
def promote_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("lab.approve_promote")),
):
    """申请灰度/上线 (admin+): SHADOW→CANARY 服务端校验门槛; CANARY→LIVE。"""
    svc = _svc(db)
    row = svc.promote(
        candidate_id=candidate_id, user_id=current_user.id, trading_mode=_mode(),
    )
    return svc.candidate_detail(row)


@router.post("/candidates/{candidate_id}/terminate", response_model=Response[LabCandidateRead])
@api_response()
def terminate_candidate(
    candidate_id: int,
    body: LabTerminateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("lab.submit_candidate")),
):
    """终止归档 → RETIRED。"""
    svc = _svc(db)
    row = svc.terminate(
        candidate_id=candidate_id, user_id=current_user.id,
        trading_mode=_mode(), reason=body.reason,
    )
    return svc.candidate_detail(row)


@router.get("/history", response_model=Response[list[LabHistoryItemRead]])
@api_response()
def lab_history(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("lab.view")),
):
    """promote/rollback/retire 时间线 (rollback 带触发原因)。"""
    return _svc(db).history(trading_mode=_mode(), limit=limit)
