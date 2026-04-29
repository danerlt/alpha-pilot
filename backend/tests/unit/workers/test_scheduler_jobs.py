"""scheduler_jobs 装配层单元测试.

只验证 KillSwitch / 缺失 risk_profile / LLM 占位 fallback 这三类
"早期 short-circuit 路径". 真实业务逻辑由对应 worker 测试覆盖.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.shared.models import Base
from src.workers import scheduler_jobs


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


# --- _build_llm: 占位 LLM key 时回退 Mock ---------------------------------

def test_build_llm_falls_back_to_mock_on_placeholder_key():
    settings = SimpleNamespace(
        LLM_BASE_URL="https://api.deepseek.com/v1",
        LLM_API_KEY="test-llm-api-key",
        LLM_MODEL="deepseek-chat",
    )
    llm = scheduler_jobs._build_llm(settings)
    # MockLLMClient 永远返回 HOLD 兜底字符串
    out = llm.complete(system="x", user="y")
    assert "HOLD" in out.raw_text


def test_build_llm_falls_back_to_mock_on_empty_key():
    settings = SimpleNamespace(
        LLM_BASE_URL="https://api.deepseek.com/v1",
        LLM_API_KEY="",
        LLM_MODEL="deepseek-chat",
    )
    llm = scheduler_jobs._build_llm(settings)
    out = llm.complete(system="x", user="y")
    assert "HOLD" in out.raw_text


# --- _parse_csv ----------------------------------------------------------

def test_parse_csv_strips_and_filters_empty():
    assert scheduler_jobs._parse_csv("BTCUSDT, ETHUSDT ,  ,SOLUSDT") == [
        "BTCUSDT", "ETHUSDT", "SOLUSDT",
    ]


def test_parse_csv_handles_empty_string():
    assert scheduler_jobs._parse_csv("") == []


# --- new_strategy_pipeline_job: KillSwitch 暂停时早退 ----------------------

def test_strategy_job_returns_early_when_kill_switch_paused(
    monkeypatch, engine, session_factory,
):
    from src.control.kill_switch.service import KillSwitchService

    # 预先 pause
    with session_factory() as s:
        KillSwitchService(s).pause(operator_user_id=1, reason="test")
        s.commit()

    monkeypatch.setattr(scheduler_jobs, "get_session_factory", lambda: session_factory)

    # 不应触达 _build_adapter / _build_llm — 用 sentinel 验证
    called = {"adapter": False, "llm": False, "pipeline": False}

    def _fail_adapter(_settings):
        called["adapter"] = True
        raise AssertionError("KillSwitch 暂停时不应调到 _build_adapter")

    def _fail_llm(_settings):
        called["llm"] = True
        raise AssertionError("KillSwitch 暂停时不应调到 _build_llm")

    def _fail_pipeline(**_kw):
        called["pipeline"] = True
        raise AssertionError("KillSwitch 暂停时不应调到 run_strategy_pipeline_once")

    monkeypatch.setattr(scheduler_jobs, "_build_adapter", _fail_adapter)
    monkeypatch.setattr(scheduler_jobs, "_build_llm", _fail_llm)
    monkeypatch.setattr(scheduler_jobs, "run_strategy_pipeline_once", _fail_pipeline)

    # 不应抛
    scheduler_jobs.new_strategy_pipeline_job()
    assert not any(called.values())


# --- new_strategy_pipeline_job: 没有 active risk_profile 时早退 -------------

def test_strategy_job_returns_early_when_no_active_risk_profile(
    monkeypatch, engine, session_factory,
):
    monkeypatch.setattr(scheduler_jobs, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(scheduler_jobs, "get_settings", lambda: SimpleNamespace(
        TRADING_MODE=SimpleNamespace(value="testnet"),
        BINANCE_API_KEY="x", BINANCE_API_SECRET="y",
        LLM_BASE_URL="https://api.deepseek.com/v1", LLM_API_KEY="test-x", LLM_MODEL="m",
        PIPELINE_SYMBOLS="BTCUSDT", PIPELINE_TIMEFRAMES="1h",
    ))

    # KillSwitch 默认 active, _load_active_risk_profile → None (空 DB)
    called = {"pipeline": False}

    def _fail_pipeline(**_kw):
        called["pipeline"] = True
        raise AssertionError("无 risk_profile 时不应触发 pipeline")

    monkeypatch.setattr(scheduler_jobs, "run_strategy_pipeline_once", _fail_pipeline)
    monkeypatch.setattr(scheduler_jobs, "_build_adapter", lambda s: object())
    monkeypatch.setattr(scheduler_jobs, "_build_llm", lambda s: object())

    scheduler_jobs.new_strategy_pipeline_job()
    assert called["pipeline"] is False
