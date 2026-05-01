"""AccountStateService — 账户余额/持仓/PnL 同步, 写 account_snapshots 表。

V0.1: 从 ExchangeAdapter 拿 USDT 可用余额; 从 positions 表加总未实现盈亏;
从 trades 表加总今日已实现盈亏。total = available + sum(market_value of open positions)。
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.execution.exchange.adapter import ExchangeAdapter
from src.shared.enums import PositionStatus
from src.models.account import AccountSnapshot
from src.models.position import Position
from src.models.trade import Trade

logger = logging.getLogger(__name__)


class AccountStateService:
    def __init__(self, session: Session, adapter: ExchangeAdapter):
        self._session = session
        self._adapter = adapter

    def sync_snapshot(
        self, *, account_id: int, trading_mode: str,
    ) -> AccountSnapshot:
        """拉余额 + 计算未实现/已实现 PnL → 写 account_snapshots 行。"""
        available = float(self._adapter.get_balance("USDT"))

        # 未实现 PnL: positions.unrealized_pnl 加总
        open_positions = self._session.execute(
            select(Position).where(
                Position.account_id == account_id,
                Position.trading_mode == trading_mode,
                Position.status == PositionStatus.OPEN.value,
            )
        ).scalars().all()
        unrealized = sum(float(p.unrealized_pnl or 0) for p in open_positions)
        # market_value 估算: quantity * (current_price 或 entry_price 兜底)
        market_value = sum(
            float(p.quantity) * float(p.current_price or p.entry_price)
            for p in open_positions
        )

        # 今日已实现 PnL: closed_at 在今天 UTC 范围内的 trades pnl 加总。
        # 不用 cast(Date) 是因为 SQLite 单测下行为不一致；用闭区间 datetime
        # 同时兼容两种后端。
        today_utc = datetime.now(tz=timezone.utc).date()
        start_today = datetime.combine(today_utc, time.min, tzinfo=timezone.utc)
        end_today = start_today + timedelta(days=1)
        today_trades = self._session.execute(
            select(Trade).where(
                Trade.account_id == account_id,
                Trade.trading_mode == trading_mode,
                Trade.closed_at >= start_today,
                Trade.closed_at < end_today,
            )
        ).scalars().all()
        daily_pnl = sum(float(t.pnl or 0) for t in today_trades)

        total = available + market_value
        daily_pnl_pct = (daily_pnl / total) if total > 0 else 0.0

        snap = AccountSnapshot(
            account_id=account_id,
            trading_mode=trading_mode,
            snapshot_at=datetime.now(tz=timezone.utc),
            total_balance_usdt=total,
            available_balance_usdt=available,
            unrealized_pnl=unrealized,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
        )
        self._session.add(snap)
        self._session.flush()
        return snap

    def get_current_balance_usdt(
        self, *, account_id: int, trading_mode: str,
    ) -> float:
        """读 account_snapshots 最新一行的 total_balance_usdt; 无则 0。"""
        snap = self._session.execute(
            select(AccountSnapshot).where(
                AccountSnapshot.account_id == account_id,
                AccountSnapshot.trading_mode == trading_mode,
            ).order_by(AccountSnapshot.snapshot_at.desc()).limit(1)
        ).scalars().first()
        return float(snap.total_balance_usdt) if snap else 0.0

    def get_daily_pnl(
        self, *, account_id: int, trading_mode: str,
    ) -> tuple[float, float]:
        """返回 (daily_pnl, daily_pnl_pct), 取最新 snapshot。"""
        snap = self._session.execute(
            select(AccountSnapshot).where(
                AccountSnapshot.account_id == account_id,
                AccountSnapshot.trading_mode == trading_mode,
            ).order_by(AccountSnapshot.snapshot_at.desc()).limit(1)
        ).scalars().first()
        if snap is None:
            return 0.0, 0.0
        return float(snap.daily_pnl), float(snap.daily_pnl_pct)
