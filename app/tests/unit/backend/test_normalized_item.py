import pytest
from app.models.normalized_item import NormalizedItem
from pydantic import ValidationError


def test_normalized_item_enforces_global_id_policy() -> None:
    with pytest.raises(ValidationError):
        NormalizedItem(
            id="wrong:ms-1",
            source="mock",
            source_label="Mock",
            source_item_id="ms-1",
            title="Item",
        )
