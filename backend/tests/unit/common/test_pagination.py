from src.common.schemas.pagination import Paginated


def test_paginated_default():
    p = Paginated[dict]()
    assert p.items == []
    assert p.total == 0
    assert p.page_index == 1
    assert p.page_size == 20
    assert p.pages == 0


def test_paginated_with_data():
    p = Paginated[dict](
        items=[{"id": 1}, {"id": 2}],
        total=42,
        page_index=2,
        page_size=20,
        pages=3,
    )
    assert len(p.items) == 2
    assert p.total == 42
    assert p.page_index == 2
    assert p.pages == 3
