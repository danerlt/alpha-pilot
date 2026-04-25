"""KillSwitchService — 全局停机/恢复开关。

状态存 system_settings (key=`kill_switch_state`, value 'paused'|'active')。
strategy_pipeline / position_monitor 启动时检查；paused 时跳过整个 cycle。
切换状态都写 audit_logs。
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.models.audit_log import AuditLog
from src.shared.models.system_setting import SystemSetting

KILL_SWITCH_KEY = "kill_switch_state"
ACTIVE = "active"
PAUSED = "paused"


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
