"""测试 log.py 的 ContextFilter 自动注入 request_id 到 LogRecord。"""
import logging

from src.utils.log import ContextFilter


def test_context_filter_injects_dash_when_no_request_id():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="x", lineno=1,
        msg="msg", args=(), exc_info=None,
    )
    f = ContextFilter()
    assert f.filter(record) is True
    assert record.request_id == "-"


def test_context_filter_keeps_existing_request_id():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="x", lineno=1,
        msg="msg", args=(), exc_info=None,
    )
    record.request_id = "abc123"
    f = ContextFilter()
    assert f.filter(record) is True
    assert record.request_id == "abc123"
