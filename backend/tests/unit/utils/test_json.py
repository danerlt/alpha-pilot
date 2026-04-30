"""测试 json 工具。"""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from src.utils.json import dumps


class _Color(Enum):
    RED = "red"


def test_dumps_datetime():
    s = dumps({"t": datetime(2026, 4, 30, 10, 23, 45)})
    assert "2026-04-30 10:23:45" in s


def test_dumps_decimal():
    s = dumps({"x": Decimal("3.14")})
    assert '"x": "3.14"' in s


def test_dumps_enum():
    s = dumps({"c": _Color.RED})
    assert '"c": "red"' in s


def test_dumps_chinese_no_ascii():
    s = dumps({"name": "持仓"})
    assert "持仓" in s
