from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any, Literal

from sqlalchemy import and_

from app.common.utils.money import parse_money_to_tenge
from app.database.models.property import Property


MAX_FLOOR_SEARCH_VALUE = 200
MAX_PROPERTY_AREA = Decimal("99999999.99")
MAX_PROPERTY_PRICE = Decimal("9999999999.99")
MIN_PRICE_TOLERANCE = Decimal("500000")
PRICE_TOLERANCE_RATE = Decimal("0.05")
QuickPropertySearchKind = Literal["phone", "price", "text", "mixed"]


@dataclass(frozen=True)
class QuickPropertySearchQuery:
    kind: QuickPropertySearchKind
    text: str
    digits: str = ""
    normalized_phone: str | None = None
    number: Decimal | None = None
    labeled_number: Decimal | None = None
    price: Decimal | None = None
    has_area_label: bool = False
    has_floor_label: bool = False
    floor_pair: tuple[int | None, int | None] = (None, None)



def normalize_search_text(value: object) -> str:
    if value is None:
        return ""
    cleaned = str(value).strip()
    if not cleaned:
        return ""
    return " ".join(cleaned.split())


def is_query_too_short(query_text: str) -> bool:
    normalized = normalize_search_text(query_text)
    if not normalized:
        return True

    digit_count = len(only_digits(normalized))
    if digit_count >= 4:
        return False

    # for text queries require at least 3 visible characters
    meaningful_len = len(normalized.replace(" ", ""))
    return meaningful_len < 3

def only_digits(value: object) -> str:
    if value is None:
        return ""
    return "".join(ch for ch in str(value) if ch.isdigit())


def _is_phone_chars_only(text: str) -> bool:
    allowed_chars = set("+() -0123456789")
    return bool(text) and all(ch in allowed_chars for ch in text)


def _normalize_kz_phone_digits(digits: str) -> str | None:
    if len(digits) == 10 and digits.startswith(("6", "7")):
        return f"7{digits}"

    if len(digits) == 11:
        if digits.startswith("7") and digits[1:2] in {"6", "7"}:
            return digits
        if digits.startswith("8") and digits[1:2] in {"6", "7"}:
            return f"7{digits[1:]}"

    if len(digits) == 12:
        return _normalize_kz_phone_digits(digits[1:]) or _normalize_kz_phone_digits(digits[-11:])

    return None


def normalize_kz_phone_query(query: object) -> str | None:
    normalized = normalize_search_text(query)
    if not _is_phone_chars_only(normalized):
        return None
    return _normalize_kz_phone_digits(only_digits(normalized))


def is_phone_like_query(query: object) -> bool:
    normalized = normalize_search_text(query)
    if not normalized:
        return False

    digits = only_digits(normalized)
    if normalize_kz_phone_query(normalized) is not None:
        return True

    if not _is_phone_chars_only(normalized) or not (4 <= len(digits) <= 9):
        return False

    if _looks_like_price_text(normalized, digits):
        return False

    return True


def normalize_phone_query(query: object) -> str:
    normalized = normalize_search_text(query)
    digits = only_digits(normalized)
    return normalize_kz_phone_query(normalized) or digits


def parse_decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    normalized = str(value).strip().replace(" ", "").replace(",", ".")
    if not normalized:
        return None
    if not re.fullmatch(r"\d+(?:\.\d+)?", normalized):
        return None
    try:
        return Decimal(normalized)
    except Exception:
        return None


def parse_first_decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    normalized = str(value).strip().replace(" ", "").replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", normalized)
    if not match:
        return None
    try:
        return Decimal(match.group(0))
    except Exception:
        return None


def parse_floor_pair(text: str) -> tuple[int | None, int | None]:
    match = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\b", text)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _has_price_label(text: str) -> bool:
    lower = text.lower()
    return any(word in lower for word in ("млн", "мил", "цена", "стоимость", "тенге", "тг", "kzt", "₸"))


def _has_money_grouping(text: str) -> bool:
    compact = re.sub(r"\s+", " ", text.strip())
    return bool(re.fullmatch(r"\d{1,3}(?: \d{3})+", compact))


def _has_text_letters(text: str) -> bool:
    return any(ch.isalpha() for ch in text)


def _is_plain_phone_fragment(text: str, digits: str) -> bool:
    if not _is_phone_chars_only(text):
        return False
    if not (4 <= len(digits) <= 9):
        return False
    return digits.startswith("7") and not _has_money_grouping(text)


def _looks_like_price_text(text: str, digits: str | None = None) -> bool:
    query_text = normalize_search_text(text)
    query_digits = digits if digits is not None else only_digits(query_text)
    normalized_number = query_text.replace(" ", "").replace(",", ".")
    number = parse_decimal_or_none(query_text)

    if normalize_kz_phone_query(query_text) is not None:
        return False
    if _is_plain_phone_fragment(query_text, query_digits):
        return False
    if _has_price_label(query_text) or _has_money_grouping(query_text):
        return True
    if number is not None and Decimal("10") <= number < Decimal("1000"):
        return True
    if re.fullmatch(r"\d+", normalized_number) and 6 <= len(query_digits) <= 10:
        return True
    return False


def should_search_price(text: str) -> bool:
    return _looks_like_price_text(text)


def _parse_price_from_search(text: str) -> Decimal | None:
    if not should_search_price(text):
        return None

    price_value = parse_money_to_tenge(text)
    if price_value is None or not (Decimal("0") <= price_value <= MAX_PROPERTY_PRICE):
        return None
    return price_value


def detect_quick_property_search_query(query: str) -> QuickPropertySearchQuery:
    query_text = normalize_search_text(query)
    digits = only_digits(query_text)
    normalized_phone = normalize_kz_phone_query(query_text)
    number = parse_decimal_or_none(query_text)
    labeled_number = None if number is not None else parse_first_decimal_or_none(query_text)
    has_area_label = _has_area_label(query_text)
    has_floor_label = _has_floor_label(query_text)
    floor_pair = parse_floor_pair(query_text)

    if normalized_phone is not None:
        return QuickPropertySearchQuery(
            kind="phone",
            text=query_text,
            digits=digits,
            normalized_phone=normalized_phone,
            floor_pair=floor_pair,
        )

    price_value = _parse_price_from_search(query_text)
    if is_phone_like_query(query_text):
        return QuickPropertySearchQuery(
            kind="phone",
            text=query_text,
            digits=digits,
            normalized_phone=digits,
            floor_pair=floor_pair,
        )

    has_text = _has_text_letters(query_text)
    has_numeric_search = number is not None or labeled_number is not None or floor_pair != (None, None)
    has_labeled_numeric_search = has_area_label or has_floor_label or floor_pair != (None, None)

    if has_text:
        kind: QuickPropertySearchKind = "mixed" if price_value is not None or has_labeled_numeric_search else "text"
    elif price_value is not None and (_has_price_label(query_text) or _has_money_grouping(query_text) or len(digits) >= 6):
        kind = "price"
    elif price_value is not None or has_numeric_search:
        kind = "mixed"
    else:
        kind = "text"

    return QuickPropertySearchQuery(
        kind=kind,
        text=query_text,
        digits=digits,
        number=number,
        labeled_number=labeled_number,
        price=price_value,
        has_area_label=has_area_label,
        has_floor_label=has_floor_label,
        floor_pair=floor_pair,
    )


def _model_has_column(name: str, available_fields: set[str]) -> bool:
    return name in available_fields


def _add_text_conditions(conditions: list[Any], search_fragment: str, available_fields: set[str]) -> None:
    if not search_fragment:
        return
    pattern = f"%{search_fragment}%"
    for field_name in (
        "title",
        "district",
        "address",
        "description",
        "owner_phone",
    ):
        if _model_has_column(field_name, available_fields):
            conditions.append(getattr(Property, field_name).ilike(pattern))


def _add_phone_conditions(conditions: list[Any], query: QuickPropertySearchQuery, available_fields: set[str]) -> None:
    phone_digits = query.normalized_phone or query.digits
    raw_digits = query.digits or phone_digits
    if phone_digits and _model_has_column("owner_phone_normalized", available_fields):
        conditions.append(Property.owner_phone_normalized.ilike(f"%{phone_digits}%"))
    if raw_digits and _model_has_column("owner_phone", available_fields):
        conditions.append(Property.owner_phone.ilike(f"%{raw_digits}%"))


def _add_nearby_numeric_conditions(conditions: list[Any], number: Decimal, available_fields: set[str]) -> None:
    _add_nearby_area_condition(conditions, number, available_fields)
    _add_nearby_floor_condition(conditions, number, available_fields)


def _add_nearby_area_condition(conditions: list[Any], number: Decimal, available_fields: set[str]) -> None:
    if number > MAX_PROPERTY_AREA:
        return
    area_tolerance = max(number * Decimal("0.1"), Decimal("5"))
    if _model_has_column("area", available_fields):
        lower_bound = max(Decimal("0"), number - area_tolerance)
        upper_bound = min(MAX_PROPERTY_AREA, number + area_tolerance)
        if lower_bound <= upper_bound:
            conditions.append(Property.area.between(lower_bound, upper_bound))


def _add_nearby_floor_condition(conditions: list[Any], number: Decimal, available_fields: set[str]) -> None:
    if number == int(number):
        int_number = int(number)
        if _model_has_column("floor", available_fields) and 1 <= int_number <= MAX_FLOOR_SEARCH_VALUE:
            conditions.append(Property.floor.between(max(1, int_number - 1), int_number + 1))


def _add_nearby_price_condition(
    conditions: list[Any],
    price_value: Decimal | None,
    available_fields: set[str],
) -> None:
    if price_value is None or not _model_has_column("price", available_fields):
        return

    price_tolerance = max(price_value * PRICE_TOLERANCE_RATE, MIN_PRICE_TOLERANCE)
    lower_bound = max(Decimal("0"), price_value - price_tolerance)
    upper_bound = min(MAX_PROPERTY_PRICE, price_value + price_tolerance)
    if lower_bound <= upper_bound:
        conditions.append(Property.price.between(lower_bound, upper_bound))


def _has_area_label(text: str) -> bool:
    lower = text.lower()
    return any(label in lower for label in ("площад", "квадрат", "кв.", "м2", "м²"))


def _has_floor_label(text: str) -> bool:
    return "этаж" in text.lower()


def build_property_search_conditions(*, search_text: str, available_fields: set[str]) -> list[Any]:
    detected = detect_quick_property_search_query(search_text)
    if not detected.text:
        return []

    conditions: list[Any] = []

    if detected.kind == "phone":
        _add_phone_conditions(conditions, detected, available_fields)
        return conditions

    if detected.kind in {"text", "mixed"}:
        _add_text_conditions(conditions, detected.text, available_fields)
        tokens = [token for token in detected.text.split() if token]
        for token in tokens:
            if token != detected.text:
                _add_text_conditions(conditions, token, available_fields)

    if detected.kind == "price":
        _add_nearby_price_condition(conditions, detected.price, available_fields)
        return conditions

    floor, building_floors = detected.floor_pair
    if floor is not None and building_floors is not None and {"floor", "building_floors"}.issubset(available_fields):
        conditions.append(and_(Property.floor == floor, Property.building_floors == building_floors))

    if detected.number is not None:
        _add_nearby_numeric_conditions(conditions, detected.number, available_fields)
    else:
        if detected.labeled_number is not None:
            if detected.has_area_label:
                _add_nearby_area_condition(conditions, detected.labeled_number, available_fields)
            if detected.has_floor_label:
                _add_nearby_floor_condition(conditions, detected.labeled_number, available_fields)

    _add_nearby_price_condition(conditions, detected.price, available_fields)

    return conditions
