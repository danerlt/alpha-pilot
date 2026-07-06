"""runtime 配置写回 settings 单例测试 (env 只做 fallback 的关键一环)。

修复回归: 旧实现 refresh 只存 manager, 从未写回 get_settings() 单例 →
前端设置页/runtime API 写入 DB 的配置实际不生效。
"""
from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.configs.app_configs import get_settings
from src.models import Base
from src.services.system.runtime_config import (
    apply_runtime_settings_refresh,
    upsert_system_setting,
)


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def _restore_settings():
    """保存/恢复被本测试改写的 settings 单例字段 (lru_cache 全局)。"""
    settings = get_settings()
    keep = {
        f: getattr(settings, f)
        for f in ("MAX_DAILY_LOSS_PCT", "BINANCE_API_KEY", "LLM_API_KEY")
    }
    yield
    for f, v in keep.items():
        setattr(settings, f, v)


def test_db_overrides_are_written_back_to_settings(session, _restore_settings, monkeypatch):
    # binance client 缓存清理在 sqlite 单测环境直接打桩
    import src.core.exchange.binance_client as bc

    monkeypatch.setattr(bc.get_binance_client, "cache_clear", lambda: None)

    settings = get_settings()
    master_key = Fernet.generate_key().decode()
    fernet = Fernet(master_key.encode())

    upsert_system_setting(session, key="risk.max_daily_loss_pct", value=0.05, fernet=fernet)
    upsert_system_setting(session, key="binance.testnet.api_key", value="DBKEY12345678", fernet=fernet)
    upsert_system_setting(session, key="llm.api_key", value="sk-db-live-key", fernet=fernet)
    session.commit()

    overrides = apply_runtime_settings_refresh(
        session, master_key=master_key,
        default_trading_mode=settings.TRADING_MODE,
    )

    assert overrides["MAX_DAILY_LOSS_PCT"] == 0.05
    # 关键断言: settings 单例已被写回 → 所有装配点 (adapter/LLM/守卫) 拿到 DB 值
    assert get_settings().MAX_DAILY_LOSS_PCT == 0.05
    assert get_settings().BINANCE_API_KEY == "DBKEY12345678"
    assert get_settings().LLM_API_KEY == "sk-db-live-key"


def test_refresh_safe_swallows_db_errors(monkeypatch):
    """DB 不可用时启动不炸 (env fallback 继续工作)。"""
    from src.services.system import runtime_config as rc

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr("src.db.session.get_db_session", _boom)
    assert rc.refresh_runtime_settings_safe(source="unit_test") is None


def test_notify_keys_are_mapped_to_settings(session, monkeypatch):
    """通知配置 (含加密 token) 从 DB 写回 settings → notifier 下一条告警生效。"""
    import src.core.exchange.binance_client as bc

    monkeypatch.setattr(bc.get_binance_client, "cache_clear", lambda: None)
    settings = get_settings()
    keep = {
        f: getattr(settings, f)
        for f in ("NOTIFY_TELEGRAM_BOT_TOKEN", "NOTIFY_TELEGRAM_CHAT_ID", "NOTIFY_MIN_SEVERITY")
    }
    master_key = Fernet.generate_key().decode()
    fernet = Fernet(master_key.encode())
    try:
        upsert_system_setting(session, key="notify.telegram.bot_token", value="123456:ABCDEF", fernet=fernet)
        upsert_system_setting(session, key="notify.telegram.chat_id", value="-100999", fernet=fernet)
        upsert_system_setting(session, key="notify.min_severity", value="critical", fernet=fernet)
        session.commit()
        # token 是 SECRET_KEYS → 加密入库
        from src.models.system_setting import SystemSetting

        row = session.query(SystemSetting).filter(
            SystemSetting.key == "notify.telegram.bot_token"
        ).one()
        assert row.is_secret is True and "ABCDEF" not in (row.encrypted_value or "")

        apply_runtime_settings_refresh(
            session, master_key=master_key, default_trading_mode=settings.TRADING_MODE,
        )
        assert get_settings().NOTIFY_TELEGRAM_BOT_TOKEN == "123456:ABCDEF"
        assert get_settings().NOTIFY_TELEGRAM_CHAT_ID == "-100999"
        assert get_settings().NOTIFY_MIN_SEVERITY == "critical"
    finally:
        for f, v in keep.items():
            setattr(settings, f, v)


def test_notification_service_channels_factory_refreshes():
    """dispatch 前按 factory 重建 channel — 前端改 token 无需重启 scheduler。"""
    from datetime import datetime, timezone

    from src.services.events.contracts import EventEnvelope
    from src.services.notification.service import NotificationService

    class _FakeChannel:
        name = "fake"

        def __init__(self):
            self.sent = []

        def send(self, message):
            self.sent.append(message)

    generation = {"n": 0}
    built = []

    def _factory():
        generation["n"] += 1
        ch = _FakeChannel()
        built.append(ch)
        return [ch]

    svc = NotificationService(channels=[], min_severity="warn", channels_factory=_factory)
    env = EventEnvelope(
        event_id="e1", occurred_at=datetime.now(timezone.utc), trace_id="t",
        event_type="circuit_breaker.triggered", payload={"reason": "daily_loss:-0.04"},
    )
    svc.dispatch(env)
    assert generation["n"] == 1  # 每次 dispatch 重建 → 拿最新配置
    assert built[-1].sent  # 告警送达新 channel
