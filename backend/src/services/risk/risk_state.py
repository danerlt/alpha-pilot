"""RiskStateService — 风控状态快照 (webapp 架构 B2)。

聚合 kill_switch / 熔断 / 日亏 / 仓位占比 / regime 为前端顶栏胶囊与
HALTED 联动所需的单一状态对象; 状态迁移点 (pause/resume/熔断触发/解除)
调 publish() 发 `risk.state` 事件, 前端也可随时 GET /api/risk/state 主动拉。

WARN 定义: 日亏超过熔断上限的一半 (未到 HALTED 但值得警示)。
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.cruds.account_crud import account_snapshot_crud
from src.cruds.account_entity_crud import risk_profile_crud
from src.cruds.position_crud import position_crud
from src.cruds.regime_crud import regime_snapshot_crud
from src.services.events.contracts import RiskState
from src.services.events.outbox import OutboxWriter
from src.services.risk.kill_switch import KillSwitchService


class RiskStateService:
    def __init__(self, session: Session, outbox: Optional[OutboxWriter] = None):
        self._session = session
        self._outbox = outbox

    def compute(self, *, trading_mode: str, account_id: int = 1) -> dict:
        halted = KillSwitchService(self._session).should_block_new_trades(
            account_id=account_id, trading_mode=trading_mode,
        )

        snap = account_snapshot_crud.find_latest(
            self._session, trading_mode=trading_mode, account_id=account_id,
        )
        day_loss_pct = float(snap.daily_pnl_pct) if snap else 0.0
        total = float(snap.total_balance_usdt) if snap else 0.0

        open_positions = position_crud.find_open(
            self._session, trading_mode=trading_mode, account_id=account_id,
        )
        market_value = sum(
            float(p.quantity) * float(p.current_price or p.entry_price)
            for p in open_positions
        )
        positions_pct = (market_value / total) if total > 0 else 0.0

        regime_row = regime_snapshot_crud.find_latest(
            self._session, trading_mode=trading_mode, account_id=account_id,
        )
        regime = regime_row.regime if regime_row else None

        if halted:
            state = "HALTED"
        else:
            profile = risk_profile_crud.find_active(self._session, account_id=account_id)
            warn_threshold = (
                -0.5 * float(profile.max_daily_loss_pct) if profile else -0.015
            )
            state = "WARN" if day_loss_pct <= warn_threshold else "OK"

        return {
            "state": state,
            "day_loss_pct": day_loss_pct,
            "positions_pct": positions_pct,
            "regime": regime,
        }

    def publish(self, *, trading_mode: str, account_id: int = 1, trace_id: str) -> dict:
        """compute + 发 risk.state 事件 (无 outbox 时只计算)。不 commit。"""
        data = self.compute(trading_mode=trading_mode, account_id=account_id)
        if self._outbox is not None:
            self._outbox.record(
                self._session,
                aggregate_type="risk_state", aggregate_id=None,
                event=RiskState(**data),
                account_id=account_id, trading_mode=trading_mode,
                trace_id=trace_id,
            )
        return data
