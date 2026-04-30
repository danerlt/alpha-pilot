"""pytest 共享 fixture / 启动 hook.

ALPHAPILOT_SKIP_SECRET_VALIDATION=1: 所有测试默认跳过 config._validate_secrets,
让 SQLite in-memory 单测不需要配 .env 真随机密钥. 这只在测试运行环境生效.
生产 / dev-server 不应设此环境变量.
"""
from __future__ import annotations

import os

# 必须在 import src.shared.config 之前设
os.environ.setdefault("ALPHAPILOT_SKIP_SECRET_VALIDATION", "1")

import pytest


@pytest.fixture(autouse=True)
def _silence_app_exception_autolog(monkeypatch):
    """单测全局静音 AppBaseException auto_log，避免日志污染输出。

    需要验证 auto_log 行为的单测可以临时 ``monkeypatch.setattr(AppBaseException, "auto_log", True)``
    覆盖回来。
    """
    try:
        from src.common.exception.errors import AppBaseException

        monkeypatch.setattr(AppBaseException, "auto_log", False)
    except ImportError:
        # 阶段 1 早期 src.common 还没建好的情况
        pass
