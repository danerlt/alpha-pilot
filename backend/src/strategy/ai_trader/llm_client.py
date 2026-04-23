"""LLMClient abstraction — DecisionSolver never imports anthropic/openai directly.

Three implementations:
  - ClaudeClient   (anthropic SDK)
  - OpenAIClient   (openai SDK)
  - MockLLMClient  (test fixture; returns a canned response)

The `complete(system, user, *, max_tokens, timeout_s)` signature is the
contract. Timeouts surface as LLMTimeout so callers can funnel them
through the standard fallback-HOLD path.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    raw_text: str
    tokens_used: int | None = None
    latency_ms: int | None = None
    model: str = ""
    provider: str = ""


class LLMTimeout(Exception):
    """Raised when the underlying SDK timed out. Callers should fall back
    to HOLD; do not retry on the hot path (the Pipeline cycle is 15 min,
    missing one cycle is cheaper than mispricing a trade)."""


class LLMClient(Protocol):
    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1024,
        timeout_s: int = 30,
    ) -> LLMResult: ...


class ClaudeClient:
    """Anthropic API wrapper."""

    def __init__(self, api_key: str, model: str):
        import anthropic  # local import so this module stays importable without anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(
        self, *, system: str, user: str,
        max_tokens: int = 1024, timeout_s: int = 30,
    ) -> LLMResult:
        start = time.monotonic()
        try:
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                timeout=timeout_s,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as e:
            if "timeout" in str(e).lower():
                raise LLMTimeout(str(e)) from e
            raise

        latency_ms = int((time.monotonic() - start) * 1000)
        text = msg.content[0].text if msg.content else ""
        usage = getattr(msg, "usage", None)
        tokens = None
        if usage is not None:
            input_t = getattr(usage, "input_tokens", 0) or 0
            output_t = getattr(usage, "output_tokens", 0) or 0
            tokens = input_t + output_t
        return LLMResult(
            raw_text=text, tokens_used=tokens, latency_ms=latency_ms,
            model=self._model, provider="claude",
        )


class OpenAIClient:
    """OpenAI Chat Completions API wrapper."""

    def __init__(self, api_key: str, model: str):
        import openai
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def complete(
        self, *, system: str, user: str,
        max_tokens: int = 1024, timeout_s: int = 30,
    ) -> LLMResult:
        start = time.monotonic()
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                timeout=timeout_s,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as e:
            if "timeout" in str(e).lower():
                raise LLMTimeout(str(e)) from e
            raise

        latency_ms = int((time.monotonic() - start) * 1000)
        text = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        tokens = None
        if usage is not None:
            tokens = getattr(usage, "total_tokens", None)
        return LLMResult(
            raw_text=text, tokens_used=tokens, latency_ms=latency_ms,
            model=self._model, provider="openai",
        )


class MockLLMClient:
    """Test fixture. Returns `canned_response` unchanged; tracks call count."""

    def __init__(self, canned_response: str = "", model: str = "mock-model", *,
                 raise_timeout_after: int | None = None):
        self._canned = canned_response
        self._model = model
        self._raise_timeout_after = raise_timeout_after
        self.call_count = 0

    def complete(self, **kwargs) -> LLMResult:
        self.call_count += 1
        if self._raise_timeout_after is not None and self.call_count > self._raise_timeout_after:
            raise LLMTimeout("simulated timeout")
        return LLMResult(
            raw_text=self._canned,
            tokens_used=42,
            latency_ms=10,
            model=self._model,
            provider="mock",
        )
