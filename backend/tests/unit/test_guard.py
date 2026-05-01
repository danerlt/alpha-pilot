"""单元测试：执行守卫 (execution_guard/guard.py) — 风控规则验证。"""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.services.strategy.decision_parser import DecisionPayload
from src.services.execution.execution_guard_service import GuardDecision, check
from src.shared.enums import Action, GuardResult, RegimeType


# ─── 测试夹具 ─────────────────────────────────────────────────────────────────

def _make_payload(
    action: Action = Action.OPEN_LONG,
    symbol: str = "BTCUSDT",
    entry_price: float = 50000.0,
    stop_loss: float = 48000.0,
    position_size_pct: float = 0.10,
) -> DecisionPayload:
    return DecisionPayload(
        symbol=symbol,
        timeframe="15m",
        action=action,
        entry_price=entry_price,
        stop_loss=stop_loss,
        position_size_pct=position_size_pct,
        confidence=0.75,
    )


def _mock_db_no_positions_no_trades() -> MagicMock:
    """返回空持仓 + 空交易记录的 mock DB。"""
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = None
    query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    return db


def _make_losing_trade(pnl: float = -100.0) -> MagicMock:
    t = MagicMock()
    t.pnl = Decimal(str(pnl))
    return t


# ─── 规则 1: 日亏损熔断 ───────────────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_daily_loss_circuit_breaker_rejects(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = _mock_db_no_positions_no_trades()
    payload = _make_payload()
    result = check(db, payload, 50000.0, "trending_up", 10000.0, -400.0, -0.04)
    assert result.result == GuardResult.REJECT
    assert "daily_loss" in result.reason


@patch("src.services.execution.execution_guard_service.get_settings")
def test_daily_loss_below_limit_does_not_reject(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = _mock_db_no_positions_no_trades()
    payload = _make_payload()
    result = check(db, payload, 50000.0, "trending_up", 10000.0, -200.0, -0.02)
    assert result.result != GuardResult.REJECT or "daily_loss" not in result.reason


# ─── 规则 2: 连续亏损熔断 ─────────────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_consecutive_losses_circuit_breaker(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = MagicMock()
    # 构造 3 笔连续亏损交易
    losing_trades = [_make_losing_trade(-100.0) for _ in range(3)]
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = losing_trades
    # 无持仓
    db.query.return_value.filter.return_value.first.return_value = None

    payload = _make_payload()
    result = check(db, payload, 50000.0, "trending_up", 10000.0, -100.0, -0.01)
    assert result.result == GuardResult.REJECT
    assert "consecutive_losses" in result.reason


@patch("src.services.execution.execution_guard_service.get_settings")
def test_two_losses_not_enough_for_circuit_breaker(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = MagicMock()
    losing_trades = [_make_losing_trade(-100.0) for _ in range(2)]  # only 2
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = losing_trades
    db.query.return_value.filter.return_value.first.return_value = None

    payload = _make_payload()
    result = check(db, payload, 50000.0, "trending_up", 10000.0, -100.0, -0.01)
    # Should not be rejected by consecutive loss rule
    assert not (result.result == GuardResult.REJECT and "consecutive_losses" in result.reason)


# ─── 规则 3: 重复开仓 REJECT ──────────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_existing_position_rejects_open_long(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    # 已有持仓
    existing_pos = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = existing_pos

    payload = _make_payload(action=Action.OPEN_LONG, symbol="BTCUSDT")
    result = check(db, payload, 50000.0, "trending_up", 10000.0, 0.0, 0.0)
    assert result.result == GuardResult.REJECT
    assert "already_open_position" in result.reason


# ─── 规则 4: 仓位上限 REJECT ──────────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_position_size_exceeds_limit_rejects(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = _mock_db_no_positions_no_trades()
    payload = _make_payload(position_size_pct=0.25)  # exceeds 0.20
    result = check(db, payload, 50000.0, "trending_up", 10000.0, 0.0, 0.0)
    assert result.result == GuardResult.REJECT
    assert "position_size_pct" in result.reason


# ─── 规则 5: 单笔风险上限 ─────────────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_single_trade_risk_exceeds_limit_rejects(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01  # 1%
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = _mock_db_no_positions_no_trades()
    # risk = |50000 - 45000| / 50000 * 0.10 = 0.10 * 0.10 = 0.01 — at limit
    # make it exceed: entry=50000, stop=40000 → risk = 0.20 * 0.10 = 0.02 > 0.01
    payload = _make_payload(entry_price=50000.0, stop_loss=40000.0, position_size_pct=0.10)
    result = check(db, payload, 50000.0, "trending_up", 10000.0, 0.0, 0.0)
    assert result.result == GuardResult.REJECT
    assert "single_risk" in result.reason


# ─── 规则 6: CHAOTIC 市场 DEGRADE ────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_chaotic_regime_degrades_open_long(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.05  # generous limit
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = _mock_db_no_positions_no_trades()
    payload = _make_payload(entry_price=50000.0, stop_loss=49000.0, position_size_pct=0.10)
    result = check(db, payload, 50000.0, RegimeType.CHAOTIC.value, 10000.0, 0.0, 0.0)
    assert result.result == GuardResult.DEGRADE
    assert result.modified_action == Action.HOLD
    assert "chaotic" in result.reason


# ─── HOLD 动作总是 PASS ───────────────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_hold_always_passes(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.01
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = _mock_db_no_positions_no_trades()
    payload = _make_payload(action=Action.HOLD)
    result = check(db, payload, 50000.0, "trending_up", 10000.0, 0.0, 0.0)
    assert result.result == GuardResult.PASS


# ─── 全部检查通过 PASS ────────────────────────────────────────────────────────

@patch("src.services.execution.execution_guard_service.get_settings")
def test_valid_open_long_passes_all_checks(mock_settings):
    mock_settings.return_value.MAX_DAILY_LOSS_PCT = 0.03
    mock_settings.return_value.MAX_CONSECUTIVE_LOSSES = 3
    mock_settings.return_value.MAX_POSITION_SIZE_PCT = 0.20
    mock_settings.return_value.MAX_SINGLE_RISK_PCT = 0.05  # generous
    mock_settings.return_value.TRADING_MODE.value = "testnet"

    db = _mock_db_no_positions_no_trades()
    payload = _make_payload(
        action=Action.OPEN_LONG,
        entry_price=50000.0,
        stop_loss=49500.0,  # 1% away
        position_size_pct=0.10,
    )
    result = check(db, payload, 50000.0, "trending_up", 10000.0, 100.0, 0.01)
    assert result.result == GuardResult.PASS
