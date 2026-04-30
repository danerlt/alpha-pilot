from pydantic import BaseModel

from src.common.api_response import api_response, to_schema
from src.common.response.response_schema import Response


class _UserOut(BaseModel):
    id: int
    name: str


def test_api_response_wraps_dict():
    @api_response()
    def view():
        return {"id": 1, "name": "Alice"}

    r: Response = view()
    assert r.success is True
    assert r.data == {"id": 1, "name": "Alice"}


def test_api_response_wraps_with_schema():
    @api_response(schema=_UserOut)
    def view():
        return {"id": 1, "name": "Alice"}

    r: Response = view()
    assert r.success is True
    assert isinstance(r.data, _UserOut)
    assert r.data.id == 1


def test_to_schema_list():
    out = to_schema([{"id": 1, "name": "A"}, {"id": 2, "name": "B"}], _UserOut)
    assert len(out) == 2
    assert all(isinstance(x, _UserOut) for x in out)


def test_to_schema_none_passthrough():
    assert to_schema(None, _UserOut) is None
