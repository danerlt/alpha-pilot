"""统一 JSON 编解码：支持 datetime / Enum / Decimal / Pydantic / dataclass。"""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class AppJSONEncoder(json.JSONEncoder):
    """支持业务常见类型的 JSON encoder。"""

    def default(self, obj: Any) -> Any:  # noqa: D401
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "model_dump"):  # Pydantic v2
            return obj.model_dump(mode="json")
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


def dumps(obj: Any, **kwargs: Any) -> str:
    """JSON 序列化。默认 ``ensure_ascii=False`` 支持中文。"""
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("cls", AppJSONEncoder)
    return json.dumps(obj, **kwargs)


def loads(s: str | bytes) -> Any:
    """JSON 反序列化。"""
    return json.loads(s)
