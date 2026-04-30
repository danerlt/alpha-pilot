from src.common.response.response_code import ErrorCode
from src.common.response.response_schema import Response, response_base


def test_error_code_format():
    assert ErrorCode.SUCCESS.code == "0"
    assert ErrorCode.NOT_FOUND.code == "400005"
    assert ErrorCode.RISK_REJECTED.code == "600002"


def test_response_success_default():
    r = Response[dict]()
    assert r.success is True
    assert r.code == "0"
    assert r.message == "成功"
    assert r.data is None


def test_response_base_success_helper():
    r = response_base.success(data={"x": 1})
    assert r.success is True
    assert r.data == {"x": 1}
    assert r.code == "0"


def test_response_base_fail_helper():
    r = response_base.fail(code=ErrorCode.NOT_FOUND.code, message="持仓不存在")
    assert r.success is False
    assert r.code == "400005"
    assert r.message == "持仓不存在"
