from app.common.utils.property_search import is_phone_like_query, normalize_phone_query


def test_is_phone_like_query_accepts_common_phone_formats() -> None:
    assert is_phone_like_query("+77758307282") is True
    assert is_phone_like_query("77758307282") is True
    assert is_phone_like_query("8 775 830 72 82") is True
    assert is_phone_like_query("(775) 830-72-82") is True


def test_is_phone_like_query_rejects_textual_queries() -> None:
    assert is_phone_like_query("абая 10") is False
    assert is_phone_like_query("свежий ремонт") is False
    assert is_phone_like_query("a7758307282") is False


def test_normalize_phone_query_keeps_digits_only() -> None:
    assert normalize_phone_query("+7 (775) 830-72-82") == "77758307282"
