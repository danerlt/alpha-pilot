"""FastAPI 路由 — 健康检查、数据查询、手动操作。"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.services.auth import create_access_token, decode_access_token, ensure_user_is_active, verify_password, hash_password
from src.shared.config import get_base_settings, get_settings
from src.shared.db import get_db
from src.shared.enums import PositionStatus, TradingMode, UserRole, UserStatus
from src.shared.runtime_config import (
    BINANCE_MAINNET_API_KEY,
    BINANCE_MAINNET_API_SECRET,
    BINANCE_TESTNET_API_KEY,
    BINANCE_TESTNET_API_SECRET,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    MAX_CONSECUTIVE_LOSSES,
    MAX_DAILY_LOSS_PCT,
    MAX_POSITION_SIZE_PCT,
    MAX_SINGLE_RISK_PCT,
    RUNTIME_MODE_KEY,
    apply_runtime_settings_refresh,
    build_fernet,
    get_runtime_config_manager,
    upsert_system_setting,
)

router = APIRouter()


class RuntimeConfigUpdate(BaseModel):
    trading_mode: TradingMode | None = None
    binance_testnet_api_key: str | None = None
    binance_testnet_api_secret: str | None = None
    binance_mainnet_api_key: str | None = None
    binance_mainnet_api_secret: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    max_position_size_pct: float | None = None
    max_daily_loss_pct: float | None = None
    max_consecutive_losses: int | None = None
    max_single_risk_pct: float | None = None


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ─── Health ───────────────────────────────────────────────────────────────────

@router.get("/")
async def root():
    return RedirectResponse(url="/health")


@router.get("/health")
@router.get("/api/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "trading_mode": settings.TRADING_MODE.value,
        "version": "0.1.0",
    }


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.replace("Bearer ", "", 1)


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    from src.shared.models.user import User

    token = _extract_bearer_token(authorization)
    secret_key = get_base_settings().APP_AUTH_SECRET_KEY
    payload = decode_access_token(token, secret_key)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return user


def require_admin(current_user=Depends(get_current_user)):
    try:
        from src.services.auth import ensure_user_is_admin
        ensure_user_is_admin(current_user.role)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return current_user


# ─── Auth ─────────────────────────────────────────────────────────────────────

@router.post("/api/auth/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    from src.shared.models.user import User

    username = payload.username.strip()
    email = payload.email.lower().strip()
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    exists = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if exists:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id), role=user.role, secret_key=get_base_settings().APP_AUTH_SECRET_KEY)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
        },
    }


@router.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    from src.shared.models.user import User

    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    user.last_login_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    token = create_access_token(subject=str(user.id), role=user.role, secret_key=get_base_settings().APP_AUTH_SECRET_KEY)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
        },
    }


@router.get("/api/auth/me")
def auth_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status,
    }


# ─── Runtime Config ───────────────────────────────────────────────────────────

@router.get("/api/config/runtime")
def get_runtime_config(db: Session = Depends(get_db)):
    base_settings = get_base_settings()
    settings = get_settings()
    raw = get_runtime_config_manager().get_raw()

    return {
        "trading_mode": settings.TRADING_MODE.value,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "max_position_size_pct": settings.MAX_POSITION_SIZE_PCT,
        "max_daily_loss_pct": settings.MAX_DAILY_LOSS_PCT,
        "max_consecutive_losses": settings.MAX_CONSECUTIVE_LOSSES,
        "max_single_risk_pct": settings.MAX_SINGLE_RISK_PCT,
        "binance_testnet_configured": bool(raw.get(BINANCE_TESTNET_API_KEY) and raw.get(BINANCE_TESTNET_API_SECRET)),
        "binance_mainnet_configured": bool(raw.get(BINANCE_MAINNET_API_KEY) and raw.get(BINANCE_MAINNET_API_SECRET)),
        "llm_api_key_configured": bool(raw.get(LLM_API_KEY)) or settings.LLM_API_KEY != base_settings.LLM_API_KEY,
        "config_source": "database_overrides" if raw else "env_defaults",
    }


@router.post("/api/config/runtime")
def update_runtime_config(payload: RuntimeConfigUpdate, db: Session = Depends(get_db)):
    base_settings = get_base_settings()
    fernet_key = base_settings.APP_CONFIG_MASTER_KEY
    fernet = build_fernet(fernet_key)

    update_map: list[tuple[str, Any, str]] = []
    if payload.trading_mode is not None:
        update_map.append((RUNTIME_MODE_KEY, payload.trading_mode.value, "当前运行模式"))
    if payload.binance_testnet_api_key:
        update_map.append((BINANCE_TESTNET_API_KEY, payload.binance_testnet_api_key, "Binance Testnet API Key"))
    if payload.binance_testnet_api_secret:
        update_map.append((BINANCE_TESTNET_API_SECRET, payload.binance_testnet_api_secret, "Binance Testnet API Secret"))
    if payload.binance_mainnet_api_key:
        update_map.append((BINANCE_MAINNET_API_KEY, payload.binance_mainnet_api_key, "Binance Mainnet API Key"))
    if payload.binance_mainnet_api_secret:
        update_map.append((BINANCE_MAINNET_API_SECRET, payload.binance_mainnet_api_secret, "Binance Mainnet API Secret"))
    if payload.llm_provider:
        update_map.append((LLM_PROVIDER, payload.llm_provider, "LLM provider"))
    if payload.llm_model:
        update_map.append((LLM_MODEL, payload.llm_model, "LLM model"))
    if payload.llm_api_key:
        update_map.append((LLM_API_KEY, payload.llm_api_key, "LLM API key"))
    if payload.max_position_size_pct is not None:
        update_map.append((MAX_POSITION_SIZE_PCT, payload.max_position_size_pct, "最大持仓比例"))
    if payload.max_daily_loss_pct is not None:
        update_map.append((MAX_DAILY_LOSS_PCT, payload.max_daily_loss_pct, "最大日亏损比例"))
    if payload.max_consecutive_losses is not None:
        update_map.append((MAX_CONSECUTIVE_LOSSES, payload.max_consecutive_losses, "连续亏损熔断笔数"))
    if payload.max_single_risk_pct is not None:
        update_map.append((MAX_SINGLE_RISK_PCT, payload.max_single_risk_pct, "单笔最大风险比例"))

    if not update_map:
        raise HTTPException(status_code=400, detail="No config fields provided")

    for key, value, description in update_map:
        upsert_system_setting(db, key=key, value=value, fernet=fernet, description=description)

    db.commit()
    apply_runtime_settings_refresh(
        db,
        master_key=base_settings.APP_CONFIG_MASTER_KEY,
        default_trading_mode=base_settings.TRADING_MODE,
    )
    return get_runtime_config(db)


# ─── Positions ────────────────────────────────────────────────────────────────

@router.get("/api/positions")
def list_positions(db: Session = Depends(get_db)):
    """列出所有开仓持仓。"""
    from src.shared.models.position import Position
    settings = get_settings()
    rows = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .order_by(Position.opened_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "symbol": p.symbol,
            "quantity": float(p.quantity),
            "entry_price": float(p.entry_price),
            "current_price": float(p.current_price or 0),
            "stop_loss": float(p.stop_loss),
            "take_profit": float(p.take_profit) if p.take_profit else None,
            "unrealized_pnl": float(p.unrealized_pnl or 0),
            "unrealized_pnl_pct": float(p.unrealized_pnl_pct or 0),
            "opened_at": p.opened_at.isoformat(),
        }
        for p in rows
    ]


@router.post("/api/positions/{position_id}/close")
def manual_close_position(position_id: int, db: Session = Depends(get_db)):
    """手动平仓（绕过 AI 风控，直接执行）。"""
    from src.services.order_execution.executor import close_long
    from src.shared.enums import TradeExitReason
    from src.shared.models.position import Position
    settings = get_settings()
    pos = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.id == position_id,
            Position.status == PositionStatus.OPEN.value,
        )
        .first()
    )
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found or already closed")
    order = close_long(db, pos, TradeExitReason.MANUAL_CLOSE)
    if order is None:
        raise HTTPException(status_code=500, detail="Failed to close position")
    return {"message": "Position closed", "order_id": order.id}


@router.post("/api/positions/close-all")
def close_all_positions(db: Session = Depends(get_db)):
    """一键全部平仓（绕过所有风控）。"""
    from src.services.order_execution.executor import close_long
    from src.shared.enums import TradeExitReason
    from src.shared.models.position import Position
    settings = get_settings()
    open_positions = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .all()
    )
    closed = []
    for pos in open_positions:
        order = close_long(db, pos, TradeExitReason.MANUAL_CLOSE)
        if order:
            closed.append(pos.id)
    return {"closed_positions": closed, "count": len(closed)}


# ─── Trades ───────────────────────────────────────────────────────────────────

@router.get("/api/trades")
def list_trades(limit: int = 50, db: Session = Depends(get_db)):
    """返回最近 N 条已完成交易记录。"""
    from src.shared.models.trade import Trade
    settings = get_settings()
    rows = (
        db.query(Trade)
        .filter(Trade.trading_mode == settings.TRADING_MODE.value)
        .order_by(Trade.closed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "quantity": float(t.quantity),
            "entry_price": float(t.entry_price),
            "exit_price": float(t.exit_price),
            "pnl": float(t.pnl),
            "pnl_pct": float(t.pnl_pct),
            "exit_reason": t.exit_reason,
            "strategy_mode": t.strategy_mode,
            "regime": t.regime,
            "opened_at": t.opened_at.isoformat(),
            "closed_at": t.closed_at.isoformat(),
            "holding_seconds": t.holding_seconds,
        }
        for t in rows
    ]


# ─── Decisions ────────────────────────────────────────────────────────────────

@router.get("/api/decisions")
def list_decisions(limit: int = 20, db: Session = Depends(get_db)):
    """返回最近 N 条 AI 决策记录。"""
    from src.shared.models.decision import AIDecision
    settings = get_settings()
    rows = (
        db.query(AIDecision)
        .filter(AIDecision.trading_mode == settings.TRADING_MODE.value)
        .order_by(AIDecision.decided_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": d.id,
            "symbol": d.symbol,
            "timeframe": d.timeframe,
            "action": d.action,
            "confidence": float(d.confidence) if d.confidence else None,
            "strategy_mode": d.strategy_mode,
            "reasoning": d.reasoning,
            "risk_note": d.risk_note,
            "is_fallback": d.is_fallback,
            "decided_at": d.decided_at.isoformat(),
        }
        for d in rows
    ]


# ─── Risk Events ──────────────────────────────────────────────────────────────

@router.get("/api/risk-events")
def list_risk_events(limit: int = 50, db: Session = Depends(get_db)):
    from src.shared.models.risk_event import RiskEvent
    settings = get_settings()
    rows = (
        db.query(RiskEvent)
        .filter(RiskEvent.trading_mode == settings.TRADING_MODE.value)
        .order_by(RiskEvent.triggered_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "symbol": r.symbol,
            "description": r.description,
            "resolved": r.resolved,
            "triggered_at": r.triggered_at.isoformat(),
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
        for r in rows
    ]


@router.post("/api/risk-events/{event_id}/resolve")
def resolve_risk_event(event_id: int, db: Session = Depends(get_db)):
    """手动解除熔断事件。"""
    from datetime import datetime, timezone
    from src.shared.models.risk_event import RiskEvent
    settings = get_settings()
    event = (
        db.query(RiskEvent)
        .filter(
            RiskEvent.trading_mode == settings.TRADING_MODE.value,
            RiskEvent.id == event_id,
        )
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Risk event not found")
    event.resolved = True
    event.resolved_at = datetime.now(tz=timezone.utc)
    db.commit()
    return {"message": "Risk event resolved", "id": event_id}


# ─── Daily Reports ────────────────────────────────────────────────────────────

@router.get("/api/reports")
def list_reports(limit: int = 30, db: Session = Depends(get_db)):
    from src.shared.models.report import DailyReport
    settings = get_settings()
    rows = (
        db.query(DailyReport)
        .filter(DailyReport.trading_mode == settings.TRADING_MODE.value)
        .order_by(DailyReport.report_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "report_date": r.report_date.isoformat(),
            "total_trades": r.total_trades,
            "winning_trades": r.winning_trades,
            "losing_trades": r.losing_trades,
            "win_rate": float(r.win_rate) if r.win_rate else None,
            "total_pnl": float(r.total_pnl),
            "total_pnl_pct": float(r.total_pnl_pct),
            "max_drawdown": float(r.max_drawdown) if r.max_drawdown else None,
            "risk_events_count": r.risk_events_count,
        }
        for r in rows
    ]


@router.post("/api/reports/generate")
def generate_report(db: Session = Depends(get_db)):
    """手动触发今日日报生成。"""
    from src.services.reporting.reporter import generate_daily_report
    report = generate_daily_report(db)
    return {"message": "Report generated", "report_date": report.report_date.isoformat()}


# ─── Account ──────────────────────────────────────────────────────────────────

@router.get("/api/account")
def get_account(db: Session = Depends(get_db)):
    """返回最新账户快照。"""
    from src.shared.models.account import AccountSnapshot
    settings = get_settings()
    snap = (
        db.query(AccountSnapshot)
        .filter(AccountSnapshot.trading_mode == settings.TRADING_MODE.value)
        .order_by(AccountSnapshot.snapshot_at.desc())
        .first()
    )
    if not snap:
        return {"message": "No account snapshot available"}
    return {
        "total_balance_usdt": float(snap.total_balance_usdt),
        "available_balance_usdt": float(snap.available_balance_usdt),
        "unrealized_pnl": float(snap.unrealized_pnl),
        "daily_pnl": float(snap.daily_pnl),
        "daily_pnl_pct": float(snap.daily_pnl_pct),
        "snapshot_at": snap.snapshot_at.isoformat(),
    }
