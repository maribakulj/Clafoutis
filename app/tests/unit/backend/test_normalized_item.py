from pydantic import ValidationError

from app.models.normalized_item import NormalizedItem


def test_normalized_item_enforces_global_id_policy() -> None:
    try:
        NormalizedItem(
            id="wrong:ms-1",
            source="mock",
            source_label="Mock",
            source_item_id="ms-1",
            title="Item",
        )
        assert False, "NormalizedItem should enforce source:source_item_id id policy"
    except ValidationError:
        pass
