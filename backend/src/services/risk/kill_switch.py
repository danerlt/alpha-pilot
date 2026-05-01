"""KillSwitchService — 全局停机/恢复开关 + 熔断查询统一入口。

两类阻塞 strategy_pipeline 开新仓的来源 (Plan 5 codereview I2 整合):
  1. 人工 KillSwitch (system_settings.kill_switch_state = 'paused')
     —— 维护 / 紧急停机, 由 Commands router 写入
  2. 自动熔断 (risk_events 当天有 CIRCUIT_BREAKER_TRIGGERED 且未 resolved)
     —— 日亏损 / 连续亏损触发, 由 PositionMonitor 写入

历史上这两个检查分散在 scheduler_jobs.is_paused 和
strategy_pipeline._circuit_breaker_active 两处, 现在统一到
should_block_new_trades(), 调用方只看一个判断结果。

position_monitor 不应被任何一种阻塞, SL/TP 必须持续运行保护已开仓位;
KillSwitch 只阻止开新仓.

切换状态都写 audit_logs。
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog
from src.models.risk_event import RiskEvent
from src.models.system_setting import SystemSetting

KILL_SWITCH_KEY = "kill_switch_state"
ACTIVE = "active"
PAUSED = "paused"
CIRCUIT_BREAKER_EVENT_TYPE = "CIRCUIT_BREAKER_TRIGGERED"


class KillSwitchService:
    def __init__(self, session: Session):
        self._session = session

    def state(self) -> str:
        """返回 'active' / 'paused'。默认 active（无配置 = 跑）。"""
        row = self._session.execute(
            select(SystemSetting).where(SystemSetting.key == KILL_SWITCH_KEY)
        ).scalars().first()
        if row is None or row.value_json is None:
            return ACTIVE
        return str(row.value_json)

    def is_paused(self) -> bool:
        return self.state() == PAUSED

    def has_unresolved_circuit_breaker(
        self, *, account_id: int, trading_mode: str,
    ) -> bool:
        """今天 (UTC) 是否存在未 resolved 的 CIRCUIT_BREAKER_TRIGGERED 事件。

        熔断口径与 PositionMonitor 写入侧保持一致 (UTC 当日窗口); 一旦写入,
        除非操作员 POST /api/commands/resolve-breaker/{id}, 当天剩余时间不会再开新仓。
        """
        today_utc = datetime.now(tz=timezone.utc).date()
        start = datetime.combine(today_utc, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        row = self._session.execute(
            select(RiskEvent).where(
                RiskEvent.account_id == account_id,
                RiskEvent.trading_mode == trading_mode,
                RiskEvent.event_type == CIRCUIT_BREAKER_EVENT_TYPE,
                RiskEvent.resolved.is_(False),
                RiskEvent.triggered_at >= start,
                RiskEvent.triggered_at < end,
            )
        ).scalars().first()
        return row is not None

    def should_block_new_trades(
        self, *, account_id: int, trading_mode: str,
    ) -> bool:
        """整合 KillSwitch + 熔断: 任一为真都不开新仓。"""
        if self.is_paused():
            return True
        return self.has_unresolved_circuit_breaker(
            account_id=account_id, trading_mode=trading_mode,
        )

    def pause(self, *, operator_user_id: int, reason: str) -> None:
        self._set(PAUSED)
        self._audit("kill_switch_pause", operator_user_id, reason, before=ACTIVE, after=PAUSED)
        self._session.flush()

    def resume(self, *, operator_user_id: int, reason: str) -> None:
        self._set(ACTIVE)
        self._audit("kill_switch_resume", operator_user_id, reason, before=PAUSED, after=ACTIVE)
        self._session.flush()

    def _set(self, value: str) -> None:
        row = self._session.execute(
            select(SystemSetting).where(SystemSetting.key == KILL_SWITCH_KEY)
        ).scalars().first()
        if row is None:
            row = SystemSetting(key=KILL_SWITCH_KEY, value_json=value, is_secret=False)
            self._session.add(row)
        else:
            row.value_json = value
        self._session.flush()

    def _audit(
        self, action: str, operator_user_id: int, reason: str,
        before: str, after: str,
    ) -> None:
        self._session.add(AuditLog(
            account_id=1,  # global (single-account V0.1)
            user_id=operator_user_id,
            action=action,
            resource_type="kill_switch",
            resource_id=KILL_SWITCH_KEY,
            before_json={"state": before, "reason": reason},
            after_json={"state": after, "reason": reason},
        ))
