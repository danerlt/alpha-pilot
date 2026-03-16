from src.shared.enums import TradingMode
from src.shared.runtime_config import (
    BINANCE_MAINNET_API_KEY,
    BINANCE_MAINNET_API_SECRET,
    MAX_CONSECUTIVE_LOSSES,
    RUNTIME_MODE_KEY,
    apply_runtime_settings_refresh,
    build_fernet,
    get_runtime_config_manager,
    upsert_system_setting,
)
from src.shared.models.base import Base
from src.shared.models.system_setting import SystemSetting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_upsert_secret_setting_encrypts_value():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[SystemSetting.__table__])
    SessionLocal = sessionmaker(engine)
    db = SessionLocal()

    fernet = build_fernet("2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=")
    row = upsert_system_setting(
        db,
        key=BINANCE_MAINNET_API_KEY,
        value="live-key",
        fernet=fernet,
        description="mainnet key",
    )
    db.commit()

    assert row.is_secret is True
    assert row.value_json is None
    assert row.encrypted_value is not None
    assert row.encrypted_value != "live-key"



def test_refresh_applies_active_mode_credentials_and_risk_overrides():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[SystemSetting.__table__])
    SessionLocal = sessionmaker(engine)
    db = SessionLocal()
    fernet = build_fernet("2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=")

    upsert_system_setting(db, key=RUNTIME_MODE_KEY, value="mainnet", fernet=fernet)
    upsert_system_setting(db, key=BINANCE_MAINNET_API_KEY, value="main-key", fernet=fernet)
    upsert_system_setting(db, key=BINANCE_MAINNET_API_SECRET, value="main-secret", fernet=fernet)
    upsert_system_setting(db, key=MAX_CONSECUTIVE_LOSSES, value=5, fernet=fernet)
    db.commit()

    overrides = apply_runtime_settings_refresh(
        db,
        master_key="2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=",
        default_trading_mode=TradingMode.TESTNET,
    )

    assert overrides["TRADING_MODE"] == "mainnet"
    assert overrides["BINANCE_API_KEY"] == "main-key"
    assert overrides["BINANCE_API_SECRET"] == "main-secret"
    assert overrides["MAX_CONSECUTIVE_LOSSES"] == 5

    manager = get_runtime_config_manager()
    raw = manager.get_raw()
    assert raw[RUNTIME_MODE_KEY] == "mainnet"
