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
