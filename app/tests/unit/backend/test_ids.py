from app.utils.ids import make_global_id, split_global_id


def test_global_id_roundtrip() -> None:
    global_id = make_global_id("mock", "ms-1")
    assert global_id == "mock:ms-1"
    assert split_global_id(global_id) == ("mock", "ms-1")


def test_split_global_id_rejects_invalid_values() -> None:
    try:
        split_global_id("invalid")
        assert False, "split_global_id should reject ids without ':'"
    except ValueError:
        pass
