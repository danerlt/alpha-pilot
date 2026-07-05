"""设置域 Schema (handoff 3.6)。GET 出参永不含明文密钥, 只回脱敏尾 4 位。"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExchangeSettingsOut(BaseModel):
    network: Literal["testnet", "mainnet"]
    api_key_masked: str | None = None
    has_secret: bool = False


class ExchangeSettingsUpdate(BaseModel):
    network: Literal["testnet", "mainnet"] | None = None
    api_key: str | None = Field(default=None, min_length=8, max_length=200)
    api_secret: str | None = Field(default=None, min_length=8, max_length=200)


class ExchangeTestOut(BaseModel):
    ok: bool
    permissions: dict | None = None  # {read, trade, withdraw}
    warning: str | None = None
    error: str | None = None


class LlmSettingsOut(BaseModel):
    model: str
    base_url: str | None = None
    api_key_masked: str | None = None
    temperature: float = 0.3
    timeout_seconds: int = 30
    agent_models: dict[str, str] = {}


class LlmSettingsUpdate(BaseModel):
    model: str | None = Field(default=None, max_length=100)
    base_url: str | None = Field(default=None, max_length=300)
    api_key: str | None = Field(default=None, min_length=8, max_length=300)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    timeout_seconds: int | None = Field(default=None, ge=5, le=300)
    agent_models: dict[str, str] | None = None


class LlmTestOut(BaseModel):
    ok: bool
    latency_ms: int | None = None
    error: str | None = None


class NotificationSettingsOut(BaseModel):
    channels: dict[str, bool]
    subscriptions: dict[str, bool]


class NotificationSettingsUpdate(BaseModel):
    channels: dict[str, bool] | None = None
    subscriptions: dict[str, bool] | None = None


class SettingsAuditContext(BaseModel):
    """内部用: PUT 审计只记脱敏摘要。"""

    changed: list[str]
    detail: dict[str, Any] = {}
