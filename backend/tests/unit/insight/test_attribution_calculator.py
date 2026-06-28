"""阶段1: 归因纯计算 (time_bucket / narrative / summary) 单测。"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from src.services.insight.attribution.calculator import (
    build_trade_narrative,
    compute_attribution_summary,
    time_bucket,
)


def _trade(symbol="BTCUSDT", pnl=10.0, pnl_pct=0.02, exit_reason="take_profit",
           regime="trending_up", strategy_mode="breakout", hour=13,
           holding_seconds=3600):
    return SimpleNamespace(
        id=1, symbol=symbol, pnl=pnl, pnl_pct=pnl_pct, exit_reason=exit_reason,
        regime=regime, strategy_mode=strategy_mode,
        closed_at=datetime(2026, 6, 26, hour, 0, tzinfo=timezone.utc),
        holding_seconds=holding_seconds,
    )


def test_time_bucket_four_sessions():
    assert time_bucket(datetime(2026, 6, 26, 3, tzinfo=timezone.utc)) == "night"      # 0-6
    assert time_bucket(datetime(2026, 6, 26, 9, tzinfo=timezone.utc)) == "morning"    # 6-12
    assert time_bucket(datetime(2026, 6, 26, 15, tzinfo=timezone.utc)) == "afternoon" # 12-18
    assert time_bucket(datetime(2026, 6, 26, 21, tzinfo=timezone.utc)) == "evening"   # 18-24


def test_narrative_contains_key_facts():
    n = build_trade_narrative(_trade(symbol="BTCUSDT", pnl=12.5, pnl_pct=0.025,
                                     exit_reason="take_profit", regime="trending_up"))
    assert "BTCUSDT" in n
    assert "trending_up" in n
    assert "12.5" in n
    assert "止盈" in n  # exit_reason 中文化


def test_narrative_handles_loss():
    n = build_trade_narrative(_trade(pnl=-5.0, pnl_pct=-0.01, exit_reason="stop_loss"))
    assert "止损" in n
    assert "-5" in n


def test_summary_empty():
    s = compute_attribution_summary([])
    assert s.total_trades == 0
    assert s.total_pnl == 0.0
    assert s.by_symbol == []
    assert s.by_exit_reason == []


def test_summary_breaks_down_by_symbol():
    trades = [
        _trade(symbol="BTCUSDT", pnl=10.0),
        _trade(symbol="BTCUSDT", pnl=-4.0, exit_reason="stop_loss"),
        _trade(symbol="ETHUSDT", pnl=6.0),
    ]
    s = compute_attribution_summary(trades)
    assert s.total_trades == 3
    assert abs(s.total_pnl - 12.0) < 1e-9
    by_sym = {b["key"]: b for b in s.by_symbol}
    assert abs(by_sym["BTCUSDT"]["pnl_sum"] - 6.0) < 1e-9
    assert by_sym["BTCUSDT"]["trade_count"] == 2
    assert abs(by_sym["BTCUSDT"]["win_rate"] - 0.5) < 1e-9
    assert abs(by_sym["ETHUSDT"]["pnl_sum"] - 6.0) < 1e-9


def test_summary_breaks_down_by_exit_reason_and_regime():
    trades = [
        _trade(exit_reason="take_profit", regime="trending_up", pnl=10.0),
        _trade(exit_reason="stop_loss", regime="ranging", pnl=-3.0),
        _trade(exit_reason="stop_loss", regime="ranging", pnl=-2.0),
    ]
    s = compute_attribution_summary(trades)
    by_exit = {b["key"]: b for b in s.by_exit_reason}
    assert by_exit["stop_loss"]["trade_count"] == 2
    assert abs(by_exit["stop_loss"]["pnl_sum"] - (-5.0)) < 1e-9
    by_regime = {b["key"]: b for b in s.by_regime}
    assert abs(by_regime["ranging"]["pnl_sum"] - (-5.0)) < 1e-9


def test_summary_sorted_by_pnl_desc():
    trades = [
        _trade(symbol="AAA", pnl=1.0),
        _trade(symbol="BBB", pnl=9.0),
        _trade(symbol="CCC", pnl=5.0),
    ]
    s = compute_attribution_summary(trades)
    keys = [b["key"] for b in s.by_symbol]
    assert keys == ["BBB", "CCC", "AAA"]  # 按 pnl_sum 降序
