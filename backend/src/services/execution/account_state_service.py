"""账户状态同步服务 — 从 Binance 拉取余额、持仓、订单状态并写入 DB。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, date

from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from src.core.exchange.binance_client import get_account_info
from src.shared.config import get_settings
from src.shared.enums import PositionStatus
from src.models.account import AccountSnapshot
from src.models.position import Position
from src.models.trade import Trade

logger = logging.getLogger(__name__)


def sync_account_snapshot(db: Session) -> AccountSnapshot:
    """拉取 Binance 账户信息，写入 account_snapshots，返回最新快照。"""
    settings = get_settings()
    info = get_account_info()

    usdt_free = 0.0
    usdt_total = 0.0
    for asset in info.get("balances", []):
        if asset["asset"] == "USDT":
            usdt_free = float(asset["free"])
            usdt_total = float(asset["free"]) + float(asset["locked"])

    open_positions = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .all()
    )
    unrealized_pnl = sum(float(p.unrealized_pnl or 0) for p in open_positions)

    today = date.today()
    daily_pnl = (
        db.query(func.sum(Trade.pnl))
        .filter(
            Trade.trading_mode == settings.TRADING_MODE.value,
            cast(Trade.closed_at, Date) == today,
        )
        .scalar()
        or 0.0
    )
    daily_pnl = float(daily_pnl)

    snapshot = AccountSnapshot(
        trading_mode=settings.TRADING_MODE.value,
        snapshot_at=datetime.now(tz=timezone.utc),
        total_balance_usdt=usdt_total,
        available_balance_usdt=usdt_free,
        unrealized_pnl=unrealized_pnl,
        daily_pnl=daily_pnl,
        daily_pnl_pct=(daily_pnl / usdt_total) if usdt_total > 0 else 0.0,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    logger.info(
        "Account snapshot saved: balance=%.2f USDT, daily_pnl=%.4f",
        usdt_total,
        daily_pnl,
    )
    return snapshot


def get_current_balance_usdt(db: Session) -> float:
    """返回最新账户快照中的可用 USDT 余额。"""
    settings = get_settings()
    snap = (
        db.query(AccountSnapshot)
        .filter(AccountSnapshot.trading_mode == settings.TRADING_MODE.value)
        .order_by(AccountSnapshot.snapshot_at.desc())
        .first()
    )
    return float(snap.available_balance_usdt) if snap else 0.0


def get_daily_pnl(db: Session) -> tuple[float, float]:
    """返回 (daily_pnl_usdt, daily_pnl_pct) from latest snapshot."""
    settings = get_settings()
    snap = (
        db.query(AccountSnapshot)
        .filter(AccountSnapshot.trading_mode == settings.TRADING_MODE.value)
        .order_by(AccountSnapshot.snapshot_at.desc())
        .first()
    )
    if snap is None:
        return 0.0, 0.0
    return float(snap.daily_pnl), float(snap.daily_pnl_pct)
