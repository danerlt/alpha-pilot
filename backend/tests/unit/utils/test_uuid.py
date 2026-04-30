"""测试 uuid 工具。"""
import re

from src.utils.uuid import get_uuid_without_hyphen


def test_get_uuid_without_hyphen_returns_32_char_hex():
    uid = get_uuid_without_hyphen()
    assert isinstance(uid, str)
    assert len(uid) == 32
    assert re.fullmatch(r"[0-9a-f]{32}", uid) is not None


def test_get_uuid_without_hyphen_unique():
    uids = {get_uuid_without_hyphen() for _ in range(100)}
    assert len(uids) == 100
