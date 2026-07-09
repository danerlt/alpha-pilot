import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.common.enums import UserRole, UserStatus
from src.configs.app_configs import AppConfig as Settings
from src.models.base import Base
from src.models.user import User
from src.services.admin_bootstrap import ensure_default_admin
from src.services.auth import hash_password


def make_db():
    engine = create_engine(
        os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"),
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine, tables=[User.__table__])
    return engine, TestingSessionLocal()


def test_ensure_default_admin_creates_user():
    engine, db = make_db()
    try:
        settings = Settings(_env_file=None, DEFAULT_ADMIN_EMAIL="danerlt001@gmail.com", DEFAULT_ADMIN_USERNAME="danerlt001", DEFAULT_ADMIN_PASSWORD="Alpha123456@#$")
        changed = ensure_default_admin(db, settings)
        user = db.query(User).filter(User.email == "danerlt001@gmail.com").first()

        assert changed is True
        assert user is not None
        assert user.username == "danerlt001"
        assert user.role == UserRole.ADMIN.value
        assert user.status == UserStatus.ACTIVE.value
    finally:
        db.close()
        engine.dispose()


def test_ensure_default_admin_promotes_existing_user_and_resets_password():
    engine, db = make_db()
    try:
        old_hash = hash_password("old-pass-123")
        existing = User(
            username="legacy",
            email="danerlt001@gmail.com",
            password_hash=old_hash,
            role=UserRole.USER.value,
            status=UserStatus.DISABLED.value,
        )
        db.add(existing)
        db.commit()

        settings = Settings(_env_file=None, DEFAULT_ADMIN_EMAIL="danerlt001@gmail.com", DEFAULT_ADMIN_USERNAME="danerlt001", DEFAULT_ADMIN_PASSWORD="Alpha123456@#$")
        changed = ensure_default_admin(db, settings)
        user = db.query(User).filter(User.email == "danerlt001@gmail.com").first()

        assert changed is True
        assert user is not None
        assert user.username == "danerlt001"
        assert user.role == UserRole.ADMIN.value
        assert user.status == UserStatus.ACTIVE.value
        assert user.password_hash != old_hash
    finally:
        db.close()
        engine.dispose()


def test_ensure_default_risk_profile_creates_and_idempotent(pg_session):
    """决策链前置:缺 active risk_profile 则每轮 skipped 不交易。用真实 PG
    (RiskProfile 时间戳 server_default 在 sqlite 不兼容)。"""
    from src.models.account_entity import RiskProfile
    from src.services.admin_bootstrap import ensure_default_risk_profile

    settings = Settings(_env_file=None)
    assert ensure_default_risk_profile(pg_session, settings, account_id=1) is True
    prof = (
        pg_session.query(RiskProfile)
        .filter(RiskProfile.account_id == 1, RiskProfile.active.is_(True))
        .first()
    )
    assert prof is not None
    assert float(prof.max_daily_loss_pct) == 0.03
    assert prof.active is True
    # 幂等:已存在不重复建
    assert ensure_default_risk_profile(pg_session, settings, account_id=1) is False
    assert (
        pg_session.query(RiskProfile)
        .filter(RiskProfile.account_id == 1)
        .count()
        == 1
    )


def test_ensure_default_symbol_configs_seeds_and_idempotent(pg_session):
    """symbol_config 表空会导致自选列表空/价格 $0.000/ws-market 4404。
    开箱按 env PIPELINE_SYMBOLS seed 默认启用项。"""
    from src.models.symbol_config import SymbolConfig
    from src.services.admin_bootstrap import ensure_default_symbol_configs

    settings = Settings(_env_file=None, PIPELINE_SYMBOLS="BTCUSDT,ETHUSDT")
    created = ensure_default_symbol_configs(pg_session, settings, account_id=1)
    assert created == 2

    rows = (
        pg_session.query(SymbolConfig)
        .order_by(SymbolConfig.sort_order.asc())
        .all()
    )
    assert [r.symbol for r in rows] == ["BTCUSDT", "ETHUSDT"]
    assert all(r.enabled is True for r in rows)
    assert rows[0].base_asset == "BTC"
    assert rows[0].quote_asset == "USDT"

    # 幂等:已有任意行则不再 seed
    assert ensure_default_symbol_configs(pg_session, settings, account_id=1) == 0
    assert pg_session.query(SymbolConfig).count() == 2


def test_ensure_default_prompt_template_seeds_and_idempotent(pg_session):
    """prompt_templates 空 → PromptComposer raise → 决策链静默 HOLD 不落库 →
    AI 决策页空。开箱 seed active ait_default 模板。变量占位符须与
    PromptComposer.compose 的 variables 对齐。"""
    from string import Template

    from src.models.prompt import PromptTemplate
    from src.services.admin_bootstrap import ensure_default_prompt_template

    settings = Settings(_env_file=None)
    assert ensure_default_prompt_template(pg_session, settings) is True

    tpl = (
        pg_session.query(PromptTemplate)
        .filter(PromptTemplate.name == "ait_default", PromptTemplate.active.is_(True))
        .first()
    )
    assert tpl is not None
    assert tpl.version == 1
    # 占位符可被 compose 提供的变量安全替换,渲染后不残留未替换的 ${var}
    variables = {
        "symbol": "BTCUSDT", "timeframe": "1h", "current_price": 63000,
        "regime": "trending_up", "indicators_json": "{}", "factors_json": "{}",
        "open_position_json": "null", "account_snapshot_json": "{}",
        "recent_experience_json": "[]",
    }
    rendered_user = Template(tpl.user_template).safe_substitute(variables)
    assert "${" not in rendered_user
    assert "BTCUSDT" in rendered_user
    # 进化机制:历史经验必须进 prompt
    assert "recent_experience_json" in tpl.user_template

    # 幂等:已存在不重复建
    assert ensure_default_prompt_template(pg_session, settings) is False
    assert (
        pg_session.query(PromptTemplate)
        .filter(PromptTemplate.name == "ait_default")
        .count()
        == 1
    )
