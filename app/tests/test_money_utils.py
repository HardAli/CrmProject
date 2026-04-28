from decimal import Decimal

from app.common.utils.money import parse_money_range_to_tenge, parse_money_to_tenge


def test_parse_money_to_tenge_cases() -> None:
    assert parse_money_to_tenge("10") == Decimal("10000000")
    assert parse_money_to_tenge("19.5") == Decimal("19500000")
    assert parse_money_to_tenge("19,5") == Decimal("19500000")
    assert parse_money_to_tenge("25") == Decimal("25000000")
    assert parse_money_to_tenge("10 млн") == Decimal("10000000")
    assert parse_money_to_tenge("19.5 млн") == Decimal("19500000")
    assert parse_money_to_tenge("500 тыс") == Decimal("500000")
    assert parse_money_to_tenge("500к") == Decimal("500000")
    assert parse_money_to_tenge("500 k") == Decimal("500000")
    assert parse_money_to_tenge("10000000") == Decimal("10000000")
    assert parse_money_to_tenge("10 000 000") == Decimal("10000000")
    assert parse_money_to_tenge("") is None
    assert parse_money_to_tenge(None) is None


def test_parse_money_range_to_tenge_cases() -> None:
    assert parse_money_range_to_tenge("15-25") == (Decimal("15000000"), Decimal("25000000"))
    assert parse_money_range_to_tenge("15 - 25") == (Decimal("15000000"), Decimal("25000000"))
    assert parse_money_range_to_tenge("от 20") == (Decimal("20000000"), None)
    assert parse_money_range_to_tenge("до 30") == (None, Decimal("30000000"))
    assert parse_money_range_to_tenge("25") == (None, Decimal("25000000"))
    assert parse_money_range_to_tenge("20+") == (Decimal("20000000"), None)
