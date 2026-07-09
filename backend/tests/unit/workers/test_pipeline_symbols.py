"""ADR-0001 C1：决策链交易标的以 symbol_configs(enabled) 为准，表空回退 env。"""
from unittest.mock import MagicMock, patch

from src.cruds import symbol_config_crud
from src.workers.scheduler_jobs import _load_pipeline_symbols


def test_load_pipeline_symbols_prefers_enabled_db_rows():
    db = MagicMock()
    settings = MagicMock(PIPELINE_SYMBOLS="ENVONLY")
    fake = [MagicMock(symbol="BTCUSDT"), MagicMock(symbol="ETHUSDT")]
    with patch.object(symbol_config_crud, "find_enabled", return_value=fake):
        result = _load_pipeline_symbols(db, settings)
    assert result == ["BTCUSDT", "ETHUSDT"]


def test_load_pipeline_symbols_falls_back_to_env_when_db_empty():
    db = MagicMock()
    settings = MagicMock(PIPELINE_SYMBOLS="BTCUSDT,ETHUSDT")
    with patch.object(symbol_config_crud, "find_enabled", return_value=[]):
        result = _load_pipeline_symbols(db, settings)
    assert result == ["BTCUSDT", "ETHUSDT"]
