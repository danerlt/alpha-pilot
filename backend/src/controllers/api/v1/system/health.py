"""Health endpoints — / / /health / /api/health."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from src.common.api_response import api_response
from src.shared.config import get_settings
from src.shared.config_diagnostics import get_runtime_credential_status

router = APIRouter()


@router.get("/")
async def root():
    # Redirect 不能包 Response[T]（不是 JSON）
    return RedirectResponse(url="/health")


@router.get("/health")
@router.get("/api/health")
@api_response()
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "trading_mode": settings.TRADING_MODE.value,
        "version": "0.1.0",
        "runtime_credentials": get_runtime_credential_status(settings),
    }
