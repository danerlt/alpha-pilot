"""Settings — /api/settings 三分区 (handoff 3.6)。全部 admin。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.controllers.dependencies import require_admin
from src.db.session import get_db
from src.schemas.settings import (
    ExchangeSettingsOut,
    ExchangeSettingsUpdate,
    ExchangeTestOut,
    LlmSettingsOut,
    LlmSettingsUpdate,
    LlmTestOut,
    NotificationSettingsOut,
    NotificationSettingsUpdate,
)
from src.services.system.app_settings import AppSettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/exchange", response_model=Response[ExchangeSettingsOut])
@api_response()
def get_exchange_settings(
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    """交易所配置 (脱敏)。"""
    return AppSettingsService(db).get_exchange()


@router.put("/exchange", response_model=Response[ExchangeSettingsOut])
@api_response()
def put_exchange_settings(
    body: ExchangeSettingsUpdate,
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    """更新交易所配置: Key 加密入库, 返回只含脱敏尾 4 位。"""
    return AppSettingsService(db).put_exchange(
        operator_user_id=current_admin.id,
        network=body.network, api_key=body.api_key, api_secret=body.api_secret,
    )


@router.post("/exchange/test", response_model=Response[ExchangeTestOut])
@api_response()
def test_exchange_settings(
    body: ExchangeSettingsUpdate,
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    """测试连接 + 权限清单 {read, trade, withdraw}; withdraw=true 返回警告。"""
    return AppSettingsService(db).test_exchange(
        network=body.network, api_key=body.api_key, api_secret=body.api_secret,
    )


@router.get("/llm", response_model=Response[LlmSettingsOut])
@api_response()
def get_llm_settings(
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    return AppSettingsService(db).get_llm()


@router.put("/llm", response_model=Response[LlmSettingsOut])
@api_response()
def put_llm_settings(
    body: LlmSettingsUpdate,
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    return AppSettingsService(db).put_llm(
        operator_user_id=current_admin.id, **body.model_dump(exclude_none=True),
    )


@router.post("/llm/test", response_model=Response[LlmTestOut])
@api_response()
def test_llm_settings(
    body: LlmSettingsUpdate,
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    return AppSettingsService(db).test_llm(
        api_key=body.api_key, model=body.model, base_url=body.base_url,
    )


@router.get("/notifications", response_model=Response[NotificationSettingsOut])
@api_response()
def get_notification_settings(
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    return AppSettingsService(db).get_notifications()


@router.put("/notifications", response_model=Response[NotificationSettingsOut])
@api_response()
def put_notification_settings(
    body: NotificationSettingsUpdate,
    db: Session = Depends(get_db), current_admin=Depends(require_admin),
):
    return AppSettingsService(db).put_notifications(
        operator_user_id=current_admin.id,
        channels=body.channels, subscriptions=body.subscriptions,
        telegram_bot_token=body.telegram_bot_token,
        telegram_chat_id=body.telegram_chat_id,
        min_severity=body.min_severity,
    )
