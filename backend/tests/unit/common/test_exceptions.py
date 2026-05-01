import logging

import pytest

from src.common.exception.errors import (
    AppBaseException,
    DBException,
    KillSwitchPausedException,
    ParamsException,
    RiskRejectedException,
    ServiceException,
)
from src.common.response.response_code import ErrorCode


def test_app_base_exception_default():
    exc = AppBaseException()
    assert exc.code == ErrorCode.SYS_ERROR.code
    assert exc.message == ErrorCode.SYS_ERROR.msg


def test_service_exception_with_message():
    exc = ServiceException(message="持仓不存在")
    assert exc.message == "持仓不存在"
    assert exc.code == ErrorCode.SERVICE_ERROR.code


def test_db_exception_with_not_found_code():
    exc = DBException(error_code=ErrorCode.NOT_FOUND, message="position id=1 not found")
    assert exc.code == ErrorCode.NOT_FOUND.code


def test_params_exception_auto_log_stack_disabled():
    """ParamsException 关闭 stack 以避免日志膨胀"""
    assert ParamsException.auto_log_stack is False


def test_business_specific_exceptions():
    e1 = KillSwitchPausedException()
    assert e1.code == ErrorCode.KILL_SWITCH_PAUSED.code

    e2 = RiskRejectedException("日内亏损超阈")
    assert e2.code == ErrorCode.RISK_REJECTED.code
    assert e2.message == "日内亏损超阈"


def test_auto_log_records_error_with_class_name(monkeypatch):
    """raise 时自动记一条 ERROR，含真实子类名。

    attach 到 root logger + force propagate，绕开 smoke test 副作用。
    """
    monkeypatch.setattr(AppBaseException, "auto_log", True)

    captured: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    exc_logger = logging.getLogger("app.exception")
    exc_logger.propagate = True
    exc_logger.setLevel(logging.DEBUG)

    root = logging.getLogger()
    handler = _Capture(level=logging.DEBUG)
    root.addHandler(handler)
    old_root_level = root.level
    root.setLevel(logging.DEBUG)

    try:
        with pytest.raises(RiskRejectedException):
            raise RiskRejectedException("test")
    finally:
        root.removeHandler(handler)
        root.setLevel(old_root_level)

    matching = [r for r in captured if "[RiskRejectedException]" in r.getMessage()]
    assert len(matching) >= 1
    assert matching[0].levelname == "ERROR"
