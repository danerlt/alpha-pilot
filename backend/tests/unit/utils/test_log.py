"""测试 log.py 的 ContextFilter 自动注入 request_id 到 LogRecord + URL 凭据打码。"""
import logging

import pytest

from src.utils.log import ContextFilter, mask_url_credentials


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


@pytest.mark.parametrize(
    "raw, expected",
    [
        # redis 空用户名 + 密码
        ("redis://:s3cret@ap-redis:6379/0", "redis://:***@ap-redis:6379/0"),
        # postgres 用户名 + 密码
        (
            "postgresql://alphapilot:pw123@ap-postgres:5432/alphapilot_dev",
            "postgresql://alphapilot:***@ap-postgres:5432/alphapilot_dev",
        ),
        # 无密码原样返回
        ("redis://localhost:6389/0", "redis://localhost:6389/0"),
        # 有用户名无密码原样返回
        ("redis://user@host:6379/0", "redis://user@host:6379/0"),
        # 非 URL 原样返回, 不崩
        ("not-a-url", "not-a-url"),
    ],
)
def test_mask_url_credentials(raw, expected):
    assert mask_url_credentials(raw) == expected


def test_mask_url_credentials_hides_real_password():
    masked = mask_url_credentials("redis://:Yj0ft7o4qZyM@ap-redis:6379/0")
    assert "Yj0ft7o4qZyM" not in masked
    assert masked == "redis://:***@ap-redis:6379/0"
