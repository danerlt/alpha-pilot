"""测试 request_id 工具函数。"""
from asgi_correlation_id import correlation_id

from src.utils.request_id import current_request_id, get_request_id


def test_get_request_id_returns_none_when_unset():
    correlation_id.set(None)
    assert get_request_id() is None


def test_get_request_id_returns_value_when_set():
    correlation_id.set("abc123def456")
    assert get_request_id() == "abc123def456"


def test_current_request_id_returns_dash_when_unset():
    correlation_id.set(None)
    assert current_request_id() == "-"


def test_current_request_id_returns_value_when_set():
    correlation_id.set("xyz789")
    assert current_request_id() == "xyz789"
