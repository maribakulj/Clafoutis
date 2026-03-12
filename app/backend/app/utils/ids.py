"""Helpers to create and parse stable global identifiers."""


def make_global_id(source: str, source_item_id: str) -> str:
    """Build stable global id using source:source_item_id format."""

    return f"{source}:{source_item_id}"


def split_global_id(global_id: str) -> tuple[str, str]:
    """Split global identifier into source and source_item_id."""

    if ":" not in global_id:
        raise ValueError("global id must include ':' separator")
    source, source_item_id = global_id.split(":", maxsplit=1)
    if not source or not source_item_id:
        raise ValueError("global id must contain source and source_item_id")
    return source, source_item_id
