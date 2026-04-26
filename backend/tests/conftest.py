"""pytest 共享 fixture / 启动 hook.

ALPHAPILOT_SKIP_SECRET_VALIDATION=1: 所有测试默认跳过 config._validate_secrets,
让 SQLite in-memory 单测不需要配 .env 真随机密钥. 这只在测试运行环境生效.
生产 / dev-server 不应设此环境变量.
"""
from __future__ import annotations

import os

# 必须在 import src.shared.config 之前设
os.environ.setdefault("ALPHAPILOT_SKIP_SECRET_VALIDATION", "1")
