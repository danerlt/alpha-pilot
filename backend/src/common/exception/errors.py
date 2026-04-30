"""异常树。所有自定义异常的基类是 AppBaseException。

抛出时自动记 ERROR 级日志，含 ``type(self).__name__`` + 错误码 + 消息 + raise 行的
file:lineno + funcname + request_id + 调用栈（可选）。

约定：
- 业务代码禁止就地 ``class XxxError(Exception)``，新语义在本文件加子类
- CRUD 抛 DBException、Service 抛 ServiceException 或具体业务子类
- 测试中通过 ``monkeypatch.setattr(AppBaseException, "auto_log", False)`` 静音
"""
from __future__ import annotations

import logging
import sys
import traceback as tb_mod
from typing import ClassVar

from src.common.response.response_code import ErrorCode

logger = logging.getLogger("app.exception")


class AppBaseException(Exception):
    auto_log: ClassVar[bool] = True
    auto_log_stack: ClassVar[bool] = True

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.SYS_ERROR,
        message: str = "",
    ) -> None:
        self.error_code = error_code
        self.code = error_code.code
        self.message = message or error_code.msg
        super().__init__(self.message)
        if self.auto_log:
            self._auto_log()

    def _auto_log(self) -> None:
        frame = sys._getframe(2)
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        funcname = frame.f_code.co_name

        try:
            from src.utils.request_id import get_request_id

            request_id = get_request_id() or "-"
        except Exception:
            request_id = "-"

        stack_str = ""
        if self.auto_log_stack:
            stack_str = "".join(tb_mod.format_stack()[:-2])

        log_fmt = "[%s] code=%s msg=%s at %s:%d in %s() request_id=%s"
        log_args: list = [
            type(self).__name__,
            self.code,
            self.message,
            filename,
            lineno,
            funcname,
            request_id,
        ]
        if stack_str:
            log_fmt += "\nCall stack:\n%s"
            log_args.append(stack_str)

        logger.error(
            log_fmt,
            *log_args,
            stacklevel=3,
            extra={
                "exc_class": type(self).__name__,
                "exc_code": self.code,
                "exc_file": filename,
                "exc_lineno": lineno,
                "exc_func": funcname,
                "request_id": request_id,
            },
        )


# ── 框架级异常 ──────────────────────────────────────────────────────────
class ServiceException(AppBaseException):
    def __init__(self, message: str = "", error_code: ErrorCode = ErrorCode.SERVICE_ERROR) -> None:
        super().__init__(error_code=error_code, message=message)


class DBException(AppBaseException):
    def __init__(self, message: str = "", error_code: ErrorCode = ErrorCode.DB_ERROR) -> None:
        super().__init__(error_code=error_code, message=message)


class ParamsException(AppBaseException):
    auto_log_stack = False  # 客户端错误，关 stack 避免日志膨胀

    def __init__(self, message: str = "") -> None:
        super().__init__(error_code=ErrorCode.PARAM_ERROR, message=message)


class RedisException(AppBaseException):
    def __init__(self, message: str = "") -> None:
        super().__init__(error_code=ErrorCode.REDIS_ERROR, message=message)


# ── alpha-pilot 业务专属 ────────────────────────────────────────────────
class KillSwitchPausedException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.KILL_SWITCH_PAUSED)


class RiskRejectedException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.RISK_REJECTED)


class IdempotencyConflictException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.IDEMPOTENCY_CONFLICT)


class InsufficientBalanceException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.INSUFFICIENT_BALANCE)


class ExchangeApiException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.EXCHANGE_API_ERROR)


class LLMResponseInvalidException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.LLM_RESPONSE_INVALID)
