"""decision_engine 双 tier 路由单测.

只覆盖 _resolve_model 的纯函数行为 (model 选择 + fast 缺失回退);
真正的 _call_llm 走外部 SDK, 由集成测试覆盖.
"""
from __future__ import annotations

from types import SimpleNamespace

from src.services.decision_engine.engine import _resolve_model


def test_resolve_model_strong_returns_main_model():
    settings = SimpleNamespace(LLM_MODEL="deepseek-v4-pro", LLM_MODEL_FAST="deepseek-v4-flash")
    assert _resolve_model(settings, "strong") == "deepseek-v4-pro"


def test_resolve_model_fast_returns_fast_model_when_set():
    settings = SimpleNamespace(LLM_MODEL="deepseek-v4-pro", LLM_MODEL_FAST="deepseek-v4-flash")
    assert _resolve_model(settings, "fast") == "deepseek-v4-flash"


def test_resolve_model_fast_falls_back_to_strong_when_unset():
    settings = SimpleNamespace(LLM_MODEL="deepseek-v4-pro", LLM_MODEL_FAST="")
    assert _resolve_model(settings, "fast") == "deepseek-v4-pro"


def test_resolve_model_fast_falls_back_when_attribute_missing():
    """老的 settings 对象可能根本没 LLM_MODEL_FAST 字段 → 回退 strong, 不报错."""
    settings = SimpleNamespace(LLM_MODEL="deepseek-v4-pro")
    assert _resolve_model(settings, "fast") == "deepseek-v4-pro"
