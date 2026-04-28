"""Tests for LLMClient abstractions.

Focus on MockLLMClient and the LLMResult dataclass contract; Claude/OpenAI
SDK wrappers are exercised in end-to-end scenarios with real credentials.
"""
from __future__ import annotations

import pytest

from src.strategy.ai_trader.llm_client import (
    LLMClients,
    LLMResult,
    LLMTimeout,
    MockLLMClient,
    build_llm_clients,
)


def test_mock_client_returns_canned_response():
    client = MockLLMClient(canned_response='{"action":"HOLD"}')
    r = client.complete(system="s", user="u")
    assert isinstance(r, LLMResult)
    assert r.raw_text == '{"action":"HOLD"}'
    assert r.provider == "mock"
    assert r.tokens_used == 42
    assert r.latency_ms == 10


def test_mock_client_tracks_call_count():
    client = MockLLMClient(canned_response="x")
    client.complete(system="a", user="b")
    client.complete(system="a", user="b")
    assert client.call_count == 2


def test_mock_client_raises_timeout_after_threshold():
    """raise_timeout_after=1 means the 2nd call onward raises LLMTimeout."""
    client = MockLLMClient(canned_response="x", raise_timeout_after=1)
    client.complete(system="s", user="u")  # first call ok
    with pytest.raises(LLMTimeout):
        client.complete(system="s", user="u")


def test_llm_result_has_provider_and_model_fields():
    r = LLMResult(raw_text="x", provider="claude", model="claude-4")
    assert r.provider == "claude"
    assert r.model == "claude-4"


# --- build_llm_clients factory: 双 tier 路由 + fallback 行为 ----------------

def test_build_llm_clients_returns_two_distinct_clients_when_fast_configured(monkeypatch):
    """LLM_MODEL_FAST 与 LLM_MODEL 不同 → strong / fast 是两个独立 OpenAIClient."""
    # 屏蔽真实 SDK 初始化, 只关心 model 路由
    constructed: list[str] = []

    class _FakeOpenAI:
        def __init__(self, **kw): pass
    import src.strategy.ai_trader.llm_client as mod
    monkeypatch.setattr(mod, "__openai_init_skipped__", True, raising=False)
    real_init = mod.OpenAIClient.__init__

    def _spy_init(self, api_key, model, base_url=None):
        constructed.append(model)
        self._client = object()
        self._model = model
    monkeypatch.setattr(mod.OpenAIClient, "__init__", _spy_init)

    clients = build_llm_clients(
        api_key="sk-test",
        base_url="https://example.com/v1",
        strong_model="model-strong",
        fast_model="model-fast",
    )
    assert isinstance(clients, LLMClients)
    assert clients.strong is not clients.fast
    assert clients.get("strong")._model == "model-strong"
    assert clients.get("fast")._model == "model-fast"
    assert constructed == ["model-strong", "model-fast"]

    # Restore
    monkeypatch.setattr(mod.OpenAIClient, "__init__", real_init)


def test_build_llm_clients_fast_falls_back_to_strong_when_unset(monkeypatch):
    """LLM_MODEL_FAST 留空 → fast 复用 strong 实例 (不构造第二份 OpenAIClient)."""
    constructed: list[str] = []
    import src.strategy.ai_trader.llm_client as mod
    real_init = mod.OpenAIClient.__init__

    def _spy_init(self, api_key, model, base_url=None):
        constructed.append(model)
        self._client = object()
        self._model = model
    monkeypatch.setattr(mod.OpenAIClient, "__init__", _spy_init)

    for fast_value in (None, "", "model-strong"):  # 空 / 空字符串 / 与 strong 同名
        constructed.clear()
        clients = build_llm_clients(
            api_key="sk-test",
            base_url=None,
            strong_model="model-strong",
            fast_model=fast_value,
        )
        assert clients.fast is clients.strong, f"fast 应当复用 strong (case={fast_value!r})"
        assert constructed == ["model-strong"]

    monkeypatch.setattr(mod.OpenAIClient, "__init__", real_init)


def test_llm_clients_get_defaults_to_strong():
    a = MockLLMClient(canned_response="a", model="ma")
    b = MockLLMClient(canned_response="b", model="mb")
    clients = LLMClients(strong=a, fast=b)
    assert clients.get() is a            # 默认 tier=strong
    assert clients.get("strong") is a
    assert clients.get("fast") is b
