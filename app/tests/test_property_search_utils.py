from app.common.utils.property_search import (
    build_property_search_conditions,
    detect_quick_property_search_query,
    is_phone_like_query,
    normalize_phone_query,
)


PROPERTY_SEARCH_FIELDS = {
    "title",
    "district",
    "address",
    "description",
    "owner_phone",
    "owner_phone_normalized",
    "price",
    "area",
    "floor",
    "building_floors",
}


def _conditions_sql(query: str) -> str:
    conditions = build_property_search_conditions(search_text=query, available_fields=PROPERTY_SEARCH_FIELDS)
    return "\n".join(str(condition).lower() for condition in conditions)


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


def test_normalize_phone_query_normalizes_kz_8_prefix() -> None:
    assert normalize_phone_query("8 708 243 61 68") == "77082436168"


def test_quick_property_search_detects_full_phone_queries_without_price() -> None:
    phone_queries = [
        "+7 708 243 6168",
        "87082436168",
        "77082436168",
        "7082436168",
        "8 708 243 61 68",
        "+7-708-243-61-68",
    ]

    for query in phone_queries:
        detected = detect_quick_property_search_query(query)
        sql = _conditions_sql(query)

        assert detected.kind == "phone"
        assert detected.normalized_phone == "77082436168"
        assert "price" not in sql
        assert "owner_phone" in sql


def test_quick_property_search_detects_price_queries() -> None:
    price_queries = [
        "18",
        "18.5",
        "18 млн",
        "18млн",
        "18500000",
        "18 500 000",
    ]

    for query in price_queries:
        sql = _conditions_sql(query)

        assert "price" in sql
        assert "between" in sql


def test_quick_property_search_text_queries_do_not_use_price() -> None:
    text_queries = [
        "Каратал",
        "Болашак 14",
        "кирпич 1989",
    ]

    for query in text_queries:
        detected = detect_quick_property_search_query(query)
        sql = _conditions_sql(query)

        assert detected.kind == "text"
        assert "price" not in sql
        assert "title" in sql
        assert "address" in sql
        assert "description" in sql
