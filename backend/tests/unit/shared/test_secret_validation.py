"""shared/config 启动密钥校验单测.

post-Plan5 安全审计 C1+C2: 防止默认/弱密钥被部到生产.
"""
from __future__ import annotations

import os

import pytest

from src.shared.config import (
    InsecureSecretError,
    Settings,
    _looks_insecure,
    _validate_secrets,
)


def test_empty_secret_is_insecure():
    assert _looks_insecure("") is True
    assert _looks_insecure(None) is True  # type: ignore[arg-type]


def test_known_default_jwt_secret_is_insecure():
    """历史默认 JWT secret 必须被识别"""
    assert _looks_insecure("alpha-pilot-auth-secret-change-me") is True


def test_known_default_fernet_key_is_insecure():
    """历史 commit 进 git 的 master key 必须被识别"""
    assert _looks_insecure("2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=") is True


def test_dev_test_master_key_is_insecure():
    """单测占位 master key 必须被识别"""
    assert _looks_insecure("ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE=") is True


def test_common_placeholder_prefixes_are_insecure():
    assert _looks_insecure("dev-only-do-not-use-in-prod") is True
    assert _looks_insecure("change-me-to-a-real-secret") is True
    assert _looks_insecure("your-secret-key-here") is True
    assert _looks_insecure("test-secret-12345") is True


def test_random_strong_key_passes():
    """合法 openssl rand -hex 32 风格的强随机不被拒"""
    strong = "a3f1b2c4e5d678901234567890abcdef0123456789abcdef0123456789abcdef"
    assert _looks_insecure(strong) is False


def test_validate_secrets_skipped_when_env_set(monkeypatch):
    """ALPHAPILOT_SKIP_SECRET_VALIDATION=1 (单测专用) 必须直接通过"""
    monkeypatch.setenv("ALPHAPILOT_SKIP_SECRET_VALIDATION", "1")
    s = Settings(_env_file=None)  # 全用 default = 全弱密钥
    _validate_secrets(s)  # should not raise


def test_validate_secrets_raises_on_default_keys(monkeypatch):
    """没设 SKIP 环境变量时, 默认 dev key 必须 abort startup"""
    monkeypatch.delenv("ALPHAPILOT_SKIP_SECRET_VALIDATION", raising=False)
    s = Settings(_env_file=None)
    with pytest.raises(InsecureSecretError) as exc_info:
        _validate_secrets(s)
    assert "APP_AUTH_SECRET_KEY" in str(exc_info.value)
    assert "APP_CONFIG_MASTER_KEY" in str(exc_info.value)


def test_validate_secrets_passes_when_overridden(monkeypatch):
    """生产场景: .env 提供了强随机两个 key, 不报错"""
    monkeypatch.delenv("ALPHAPILOT_SKIP_SECRET_VALIDATION", raising=False)
    monkeypatch.setenv(
        "APP_AUTH_SECRET_KEY",
        "a3f1b2c4e5d678901234567890abcdef0123456789abcdef0123456789abcdef",
    )
    # 生成一个非默认的合法 Fernet key
    monkeypatch.setenv(
        "APP_CONFIG_MASTER_KEY",
        "cHJvZHVjdGlvbl9rZXlfd2l0aF8zMl9ieXRlc19pbl9pdF9oZXJlIQ==",
    )
    s = Settings(_env_file=None)
    _validate_secrets(s)  # should not raise
