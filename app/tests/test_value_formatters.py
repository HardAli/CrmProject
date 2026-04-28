from __future__ import annotations

from decimal import Decimal

from app.common.utils.formatters import format_area, format_area_compact
from app.common.utils.value_parsers import parse_decimal_or_none


def test_format_area_plain_decimal_without_scientific_notation() -> None:
    assert format_area(Decimal("1.3E+2")) == "130 м²"
    assert format_area(Decimal("130.00")) == "130 м²"
    assert format_area(Decimal("10.50")) == "10.5 м²"


def test_format_area_compact() -> None:
    assert format_area_compact(Decimal("130")) == "130м²"
    assert format_area_compact(Decimal("58.60")) == "58.6м²"


def test_parse_decimal_or_none_with_area_units() -> None:
    assert parse_decimal_or_none("10,5 м²") == Decimal("10.5")
    assert parse_decimal_or_none("10 м2") == Decimal("10")
    assert parse_decimal_or_none("площадь кухни 13.1 кв.м") == Decimal("13.1")
