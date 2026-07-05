"""Agent — /api/agent Pilot AI 对话域 (handoff 3.4)。

POST /api/agent/chat 是 SSE 流 (text/event-stream), 不走 Response envelope
(与 WS 同理); history / confirm 走标准 envelope。
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import (
    get_adapter,
    get_current_user,
    get_llm_client,
    require_admin,
)
from src.db.session import get_db
from src.schemas.system_read import AgentActionConfirmOut, AgentHistoryItemRead
from src.services.agent.pilot_agent import PilotAgentService

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentChatCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def _trading_mode() -> str:
    mode = get_settings().TRADING_MODE
    return mode.value if hasattr(mode, "value") else mode


@router.post("/chat")
def agent_chat(
    body: AgentChatCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    adapter=Depends(get_adapter),
    llm=Depends(get_llm_client),
):
    """Pilot AI 对话 — SSE 流式: tool_call → delta → done (要求登录)。"""
    settings = get_settings()
    svc = PilotAgentService(db, llm, adapter)

    def _sse():
        for ev in svc.chat(
            message=body.message, user_id=current_user.id,
            trading_mode=_trading_mode(),
            timeout_s=int(getattr(settings, "LLM_TIMEOUT_SECONDS", 30)),
        ):
            yield (
                f"event: {ev['event']}\n"
                f"data: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        _sse(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=Response[list[AgentHistoryItemRead]])
@api_response()
def agent_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    adapter=Depends(get_adapter),
    llm=Depends(get_llm_client),
):
    """会话历史 (要求登录)。"""
    return PilotAgentService(db, llm, adapter).history(limit=limit)


@router.post("/actions/{action_id}/confirm", response_model=Response[AgentActionConfirmOut])
@api_response()
def confirm_agent_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
    adapter=Depends(get_adapter),
    llm=Depends(get_llm_client),
):
    """人工确认 Agent 提议的配置修改 (admin): 白名单复核 + 应用 + 审计。"""
    return PilotAgentService(db, llm, adapter).confirm_action(
        action_id=action_id, admin_user_id=current_admin.id,
    )