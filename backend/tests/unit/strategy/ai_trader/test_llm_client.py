"""Tests for LLMClient abstractions.

Focus on MockLLMClient and the LLMResult dataclass contract; Claude/OpenAI
SDK wrappers are exercised in end-to-end scenarios with real credentials.
"""
from __future__ import annotations

import pytest

from src.core.llm.client import (
    LLMResult,
    LLMTimeout,
    MockLLMClient,
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
