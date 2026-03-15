from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from src.shared.config import get_settings

router = APIRouter()


@router.get("/")
async def root():
    return RedirectResponse(url="/health")


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "trading_mode": settings.TRADING_MODE.value,
        "version": "0.1.0",
    }
