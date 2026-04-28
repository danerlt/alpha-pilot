"""LLMClient abstraction — DecisionSolver never imports openai directly.

只支持 OpenAI 兼容协议 (含 DeepSeek / vLLM / 任意自托管 OpenAI-compatible endpoint),
通过 base_url + api_key + model 三元组配置。

The `complete(system, user, *, max_tokens, timeout_s)` signature is the
contract. Timeouts surface as LLMTimeout so callers can funnel them
through the standard fallback-HOLD path.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Literal, Protocol

logger = logging.getLogger(__name__)

# 模型 tier — strong 走主决策 (LLM_MODEL), fast 走轻量任务 (LLM_MODEL_FAST).
# Literal 让调用方在静态检查阶段就被强制写对 tier 名.
LLMTier = Literal["strong", "fast"]


@dataclass
class LLMResult:
    raw_text: str
    tokens_used: int | None = None
    latency_ms: int | None = None
    model: str = ""
    provider: str = "openai"


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


class OpenAIClient:
    """OpenAI Chat Completions API wrapper (兼容 DeepSeek / 任意 OpenAI 协议端点)."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        import openai
        kwargs: dict[str, object] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = openai.OpenAI(**kwargs)
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


@dataclass
class LLMClients:
    """双 tier LLM 客户端容器.

    - strong: 主决策 (DecisionSolver / decision_engine), 必须存在.
    - fast:   轻量场景 (摘要 / 分类 / 重试降级 等). 配置缺失时 fallback=strong,
              这样调用方写 `clients.fast` 永远拿得到一个可用客户端,
              不需要每个 caller 都重复兜底逻辑.

    用 `get(tier)` 按 tier 字符串路由; 未来加新 tier 只改这里一处.
    """
    strong: "LLMClient"
    fast: "LLMClient"

    def get(self, tier: LLMTier = "strong") -> "LLMClient":
        if tier == "fast":
            return self.fast
        return self.strong


def build_llm_clients(
    *,
    api_key: str,
    base_url: str | None,
    strong_model: str,
    fast_model: str | None,
) -> LLMClients:
    """Factory: 根据配置构造 strong + fast 两个 OpenAI 兼容客户端.

    - strong_model 必填.
    - fast_model 留空 (None / "" / 与 strong 相同) 时, fast 复用 strong 实例,
      调用方无须感知, 也不会多花一份 HTTP client 资源.
    """
    strong = OpenAIClient(api_key=api_key, model=strong_model, base_url=base_url)
    if not fast_model or fast_model == strong_model:
        logger.info(
            "LLM fast tier fallback to strong (model=%s); set LLM_MODEL_FAST to differentiate",
            strong_model,
        )
        fast: LLMClient = strong
    else:
        fast = OpenAIClient(api_key=api_key, model=fast_model, base_url=base_url)
    return LLMClients(strong=strong, fast=fast)


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
