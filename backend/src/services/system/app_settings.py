"""AppSettingsService — 设置三分区 (handoff 3.6)。

存储复用 runtime_config 的 system_settings + Fernet 加密机制:
  - 交易所: runtime.trading_mode + binance.{network}.api_key/secret (加密)
  - LLM:   llm.model / llm.base_url / llm.api_key (加密) / llm.temperature /
           llm.timeout_seconds / llm.agent_models (per-agent 模型分工)
  - 通知:  notify.channels / notify.subscriptions / notify.min_severity /
           notify.telegram.bot_token (加密) / notify.telegram.chat_id
           —— notifier 每次告警按当前 settings 重建 channel, 改完即生效

安全: 任何 GET 永不回明文 (只回 ****尾4位); PUT 写 AuditLog 且审计体不含明文;
真实密钥只经 API 写入 DB, 不写 env 文件 (遵守仓库 env 黑白名单)。
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from sqlalchemy.orm import Session

from src.common.exception.errors import ServiceException
from src.configs.app_configs import get_settings
from src.models.audit_log import AuditLog
from src.models.system_setting import SystemSetting
from src.services.system.runtime_config import (
    apply_runtime_settings_refresh,
    build_fernet,
    upsert_system_setting,
)

logger = logging.getLogger(__name__)

_LLM_DEFAULT_TEMPERATURE = 0.3
_DEFAULT_CHANNELS = {"telegram": False, "discord": False}
_DEFAULT_SUBSCRIPTIONS = {
    "circuit_breaker": True, "order_filled": True,
    "position_closed": True, "daily_report": False,
}


def _mask(value: str | None) -> str | None:
    if not value:
        return None
    return f"****{value[-4:]}"


class AppSettingsService:
    def __init__(
        self,
        session: Session,
        *,
        adapter_factory: Callable[..., Any] | None = None,
        llm_factory: Callable[..., Any] | None = None,
    ):
        self._session = session
        self._settings = get_settings()
        self._fernet = build_fernet(self._settings.APP_CONFIG_MASTER_KEY)
        self._adapter_factory = adapter_factory or self._default_adapter_factory
        self._llm_factory = llm_factory or self._default_llm_factory

    # ── 存储读写基元 ────────────────────────────────────────────────────

    def _read(self, key: str) -> Any:
        row = self._session.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row is None:
            return None
        if row.is_secret and row.encrypted_value:
            try:
                return self._fernet.decrypt(row.encrypted_value.encode()).decode()
            except Exception:  # noqa: BLE001
                logger.warning("decrypt failed for %s", key)
                return None
        return row.value_json

    def _write(self, changes: dict[str, Any]) -> None:
        for key, value in changes.items():
            upsert_system_setting(
                self._session, key=key, value=value, fernet=self._fernet,
                description="settings api",
            )

    def _audit(self, *, operator_user_id: int, section: str, changed: list[str]) -> None:
        self._session.add(AuditLog(
            account_id=1, user_id=operator_user_id,
            action=f"settings_update_{section}", resource_type="system_setting",
            resource_id=section, after_json={"changed": changed},
        ))
        self._session.flush()

    def _refresh(self) -> None:
        try:
            apply_runtime_settings_refresh(
                self._session,
                master_key=self._settings.APP_CONFIG_MASTER_KEY,
                default_trading_mode=self._settings.TRADING_MODE,
            )
        except Exception:  # noqa: BLE001
            logger.warning("runtime settings refresh failed (non-fatal)", exc_info=True)

    def _network(self) -> str:
        stored = self._read("runtime.trading_mode")
        if stored in ("testnet", "mainnet"):
            return stored
        mode = self._settings.TRADING_MODE
        return mode.value if hasattr(mode, "value") else mode

    # ── 交易所 ──────────────────────────────────────────────────────────

    def get_exchange(self) -> dict:
        network = self._network()
        api_key = self._read(f"binance.{network}.api_key")
        secret = self._read(f"binance.{network}.api_secret")
        return {
            "network": network,
            "api_key_masked": _mask(api_key),
            "has_secret": bool(secret),
        }

    def put_exchange(
        self, *, operator_user_id: int,
        network: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> dict:
        changes: dict[str, Any] = {}
        target = network or self._network()
        if network is not None:
            changes["runtime.trading_mode"] = network
        if api_key is not None:
            changes[f"binance.{target}.api_key"] = api_key
        if api_secret is not None:
            changes[f"binance.{target}.api_secret"] = api_secret
        if not changes:
            raise ServiceException("没有需要更新的字段")
        self._write(changes)
        self._audit(
            operator_user_id=operator_user_id, section="exchange",
            changed=sorted(changes),  # 只记键名, 不记明文
        )
        self._session.commit()
        self._refresh()
        return self.get_exchange()

    def test_exchange(
        self, *, network: str | None = None,
        api_key: str | None = None, api_secret: str | None = None,
    ) -> dict:
        target = network or self._network()
        key = api_key or self._read(f"binance.{target}.api_key") or self._settings.BINANCE_API_KEY
        secret = api_secret or self._read(f"binance.{target}.api_secret") or self._settings.BINANCE_API_SECRET
        if not key or not secret:
            return {"ok": False, "error": "缺少 API Key/Secret"}
        try:
            adapter = self._adapter_factory(
                api_key=key, api_secret=secret, trading_mode=target,
            )
            # raise_on_error: 让真实异常 (币安错误码/网络) 透出到前端, 而非笼统 None
            perms = adapter.get_account_permissions(raise_on_error=True)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:200]}
        if perms is None:
            return {"ok": False, "error": "连接失败或 Key 无效"}
        warning = None
        if perms.get("withdraw"):
            warning = "该 Key 带提现权限 — 强烈建议在交易所侧关闭提现后再使用"
        return {"ok": True, "permissions": perms, "warning": warning}

    # ── LLM ────────────────────────────────────────────────────────────

    def get_llm(self) -> dict:
        api_key = self._read("llm.api_key") or self._settings.LLM_API_KEY
        return {
            "model": self._read("llm.model") or self._settings.LLM_MODEL,
            "base_url": self._read("llm.base_url") or self._settings.LLM_BASE_URL,
            "api_key_masked": _mask(api_key),
            "temperature": self._read("llm.temperature") or _LLM_DEFAULT_TEMPERATURE,
            "timeout_seconds": (
                self._read("llm.timeout_seconds")
                or int(getattr(self._settings, "LLM_TIMEOUT_SECONDS", 30))
            ),
            "agent_models": self._read("llm.agent_models") or {},
        }

    def put_llm(self, *, operator_user_id: int, **fields: Any) -> dict:
        keymap = {
            "model": "llm.model", "base_url": "llm.base_url",
            "api_key": "llm.api_key", "temperature": "llm.temperature",
            "timeout_seconds": "llm.timeout_seconds", "agent_models": "llm.agent_models",
        }
        changes = {
            keymap[f]: v for f, v in fields.items() if v is not None and f in keymap
        }
        if not changes:
            raise ServiceException("没有需要更新的字段")
        self._write(changes)
        self._audit(
            operator_user_id=operator_user_id, section="llm", changed=sorted(changes),
        )
        self._session.commit()
        self._refresh()
        return self.get_llm()

    def test_llm(
        self, *, api_key: str | None = None,
        model: str | None = None, base_url: str | None = None,
    ) -> dict:
        cfg = self.get_llm()
        key = api_key or self._read("llm.api_key") or self._settings.LLM_API_KEY
        if not key:
            return {"ok": False, "error": "缺少 LLM API Key"}
        try:
            client = self._llm_factory(
                api_key=key,
                model=model or cfg["model"],
                base_url=base_url or cfg["base_url"],
            )
            start = time.monotonic()
            client.complete(system="You are a ping service.", user="回复 pong", max_tokens=8, timeout_s=15)
            return {"ok": True, "latency_ms": int((time.monotonic() - start) * 1000)}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:200]}

    # ── 通知 ────────────────────────────────────────────────────────────

    def get_notifications(self) -> dict:
        token = self._read("notify.telegram.bot_token")
        return {
            "channels": {**_DEFAULT_CHANNELS, **(self._read("notify.channels") or {})},
            "subscriptions": {
                **_DEFAULT_SUBSCRIPTIONS, **(self._read("notify.subscriptions") or {}),
            },
            "telegram_bot_token_masked": _mask(token),
            "telegram_chat_id": self._read("notify.telegram.chat_id"),
            "min_severity": self._read("notify.min_severity")
            or getattr(self._settings, "NOTIFY_MIN_SEVERITY", "warn"),
        }

    def put_notifications(
        self, *, operator_user_id: int,
        channels: dict | None = None, subscriptions: dict | None = None,
        telegram_bot_token: str | None = None, telegram_chat_id: str | None = None,
        min_severity: str | None = None,
    ) -> dict:
        """通知配置入库 (token Fernet 加密)。channels.telegram 开关语义:
        配置 token 即启用, 关闭请清空 token (前端开关对应清 token)。"""
        changes: dict[str, Any] = {}
        if channels is not None:
            changes["notify.channels"] = {**self.get_notifications()["channels"], **channels}
        if subscriptions is not None:
            changes["notify.subscriptions"] = {
                **self.get_notifications()["subscriptions"], **subscriptions,
            }
        if telegram_bot_token is not None:
            changes["notify.telegram.bot_token"] = telegram_bot_token
        if telegram_chat_id is not None:
            changes["notify.telegram.chat_id"] = telegram_chat_id
        if min_severity is not None:
            changes["notify.min_severity"] = min_severity
        if not changes:
            raise ServiceException("没有需要更新的字段")
        self._write(changes)
        self._audit(
            operator_user_id=operator_user_id, section="notifications",
            changed=sorted(changes),
        )
        self._session.commit()
        self._refresh()
        return self.get_notifications()

    # ── 默认工厂 ────────────────────────────────────────────────────────

    @staticmethod
    def _default_adapter_factory(**kwargs):
        from src.core.exchange.binance_adapter import BinanceAdapter

        return BinanceAdapter(**kwargs)

    @staticmethod
    def _default_llm_factory(**kwargs):
        from src.core.llm.client import OpenAIClient

        return OpenAIClient(**kwargs)
