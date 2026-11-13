import pytest
from pydantic import BaseModel, ValidationError

from prontuario_backend.views.pagination import PageResponse, PaginationParams


class ItemResponse(BaseModel):
    name: str


def test_pagination_defaults_and_boundaries():
    assert PaginationParams().model_dump() == {"limit": 20, "offset": 0}
    assert PaginationParams(limit=100, offset=100000).model_dump() == {
        "limit": 100,
        "offset": 100000,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"limit": 0},
        {"limit": -1},
        {"limit": 101},
        {"limit": "invalid"},
        {"limit": 1.5},
        {"offset": -1},
        {"offset": 100001},
        {"offset": "invalid"},
        {"sort": "unknown"},
    ],
)
def test_pagination_rejects_unbounded_invalid_or_unknown_inputs(payload):
    with pytest.raises(ValidationError):
        PaginationParams.model_validate(payload)


def test_typed_page_filters_private_item_fields():
    page = PageResponse[ItemResponse](
        items=[{"name": "isolated-item", "hash_senha": "must-not-escape"}],
        total=1,
        limit=20,
        offset=0,
    )
    assert page.model_dump() == {
        "items": [{"name": "isolated-item"}],
        "total": 1,
        "limit": 20,
        "offset": 0,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {
            "items": [{"name": "first"}, {"name": "second"}],
            "limit": 1,
            "offset": 0,
            "total": 2,
        },
        {"items": [{"name": "isolated-item"}], "limit": 20, "offset": 2, "total": 2},
        {"items": [], "limit": 20, "offset": 0, "total": -1},
    ],
)
def test_response_page_rejects_inconsistent_counts(payload):
    with pytest.raises(ValidationError):
        PageResponse[ItemResponse].model_validate(payload)


def test_empty_page_can_have_offset_beyond_the_total():
    page = PageResponse[ItemResponse](items=[], total=0, limit=20, offset=20)
    assert page.items == [] and page.offset == 20
