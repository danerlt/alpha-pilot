"""向后兼容 shim — 旧代码 ``from src.app.app import app`` 仍然工作。

新代码请用 ``from src.app import app``（提级到 src.app 包根级，模板规范）。
本文件在阶段 4 controllers 重组完成后会被删除。
"""
from src.app import app, create_app, lifespan  # noqa: F401

__all__ = ["app", "create_app", "lifespan"]
