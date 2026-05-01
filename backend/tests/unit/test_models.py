from src.models import (
    Candle, AccountSnapshot, IndicatorSnapshot,
    RegimeSnapshot, Position, AIDecision,
    Order, Trade, RiskEvent, ExperienceRecord, DailyReport, SystemSetting, User, SymbolConfig, AuditLog
)
from src.common.enums import TradingMode


def test_all_models_importable():
    """所有模型可正常导入"""
    assert Candle.__tablename__ == "candles"
    assert AccountSnapshot.__tablename__ == "account_snapshots"
    assert IndicatorSnapshot.__tablename__ == "indicator_snapshots"
    assert RegimeSnapshot.__tablename__ == "regime_snapshots"
    assert Position.__tablename__ == "positions"
    assert AIDecision.__tablename__ == "ai_decisions"
    assert Order.__tablename__ == "orders"
    assert Trade.__tablename__ == "trades"
    assert RiskEvent.__tablename__ == "risk_events"
    assert ExperienceRecord.__tablename__ == "experience_store"
    assert DailyReport.__tablename__ == "daily_reports"
    assert SystemSetting.__tablename__ == "system_settings"
    assert User.__tablename__ == "users"
    assert SymbolConfig.__tablename__ == "symbol_configs"
    assert AuditLog.__tablename__ == "audit_logs"


def test_trading_mode_column_exists():
    """所有表含 trading_mode 列（testnet/mainnet 数据完全隔离）"""
    for model in [
        Candle, AccountSnapshot, IndicatorSnapshot, RegimeSnapshot,
        Position, AIDecision, Order, Trade, RiskEvent, ExperienceRecord, DailyReport,
    ]:
        assert hasattr(model, "trading_mode"), f"{model.__name__} missing trading_mode"
