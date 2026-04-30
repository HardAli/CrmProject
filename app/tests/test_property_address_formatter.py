from __future__ import annotations

from app.common.formatters.property_address_formatter import format_property_address_for_display


def test_removes_duplicated_district_and_compacts_house() -> None:
    assert format_property_address_for_display("Жастар", "Жастар 7") == "д7"
    assert format_property_address_for_display("Самал", "Самал 25") == "д25"
    assert format_property_address_for_display("Каратал", "Каратал 37") == "д37"


def test_removes_microdistrict_prefix_when_district_is_same() -> None:
    assert format_property_address_for_display("Жастар", "мкр Жастар, дом 7") == "д7"


def test_formats_street_and_house_compactly() -> None:
    assert format_property_address_for_display("Самал", "улица Абая 15") == "ул. Абая, д15"


def test_empty_address_fallback() -> None:
    assert format_property_address_for_display("Ынтымак", "") == "-"


def test_keeps_address_when_district_not_repeated() -> None:
    assert format_property_address_for_display("Ынтымак", "проспект Тауке хана, 40") == "проспект Тауке хана, 40"
