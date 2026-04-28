from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import re
from typing import Any

from sqlalchemy import and_, func

from app.common.utils.money import parse_money_to_tenge
from app.database.models.property import Property


def only_digits(value: object) -> str:
    if value is None:
        return ""
    return "".join(ch for ch in str(value) if ch.isdigit())


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


def parse_floor_pair(text: str) -> tuple[int | None, int | None]:
    match = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\b", text)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def parse_rooms_from_search(text: str) -> int | None:
    lower = text.lower().strip()
    match = re.search(r"\b([1-9]|10)\s*(?:-?х|ком(?:н|нат)?)", lower)
    if match:
        return int(match.group(1))

    synonyms = {
        "однушка": 1,
        "двушка": 2,
        "трешка": 3,
        "трёшка": 3,
    }
    for word, rooms in synonyms.items():
        if word in lower:
            return rooms

    if re.fullmatch(r"\d+", lower):
        parsed = int(lower)
        if 1 <= parsed <= 10:
            return parsed

    return None


def should_search_price(text: str) -> bool:
    lower = text.lower().strip()
    if any(word in lower for word in ("млн", "мил", "цена", "стоимость")):
        return True

    normalized = lower.replace(",", ".").replace(" ", "")
    if re.fullmatch(r"\d+\.\d+", normalized):
        return True

    if re.fullmatch(r"\d+", normalized):
        number = int(normalized)
        if len(normalized) >= 6:
            return True
        return number >= 10

    digits = only_digits(normalized)
    return bool(digits and len(digits) >= 6)


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
        "link",
        "building_material",
        "status",
    ):
        if _model_has_column(field_name, available_fields):
            conditions.append(getattr(Property, field_name).ilike(pattern))


def _extract_id_from_search(text: str) -> int | None:
    normalized = text.strip().lower()
    if normalized.startswith("#") and normalized[1:].isdigit():
        return int(normalized[1:])

    id_match = re.match(r"^id\s*[:#]?\s*(\d+)$", normalized)
    if id_match:
        return int(id_match.group(1))

    return None


def build_property_search_conditions(*, search_text: str, available_fields: set[str]) -> list[Any]:
    query_text = search_text.strip()
    if not query_text:
        return []

    conditions: list[Any] = []
    _add_text_conditions(conditions, query_text, available_fields)

    tokens = [token for token in query_text.split() if token]
    for token in tokens:
        if token != query_text:
            _add_text_conditions(conditions, token, available_fields)

    query_digits = only_digits(query_text)
    if query_digits and _model_has_column("owner_phone", available_fields):
        phone_digits_expr = func.regexp_replace(Property.owner_phone, r"\D", "", "g")
        conditions.append(phone_digits_expr.ilike(f"%{query_digits}%"))

    floor, building_floors = parse_floor_pair(query_text)
    if floor is not None and building_floors is not None and {"floor", "building_floors"}.issubset(available_fields):
        conditions.append(and_(Property.floor == floor, Property.building_floors == building_floors))

    rooms = parse_rooms_from_search(query_text)
    if rooms is not None and _model_has_column("rooms", available_fields):
        conditions.append(Property.rooms == rooms)

    number = parse_decimal_or_none(query_text)
    if number is not None:
        delta = Decimal("0.5")
        if _model_has_column("area", available_fields):
            conditions.append(Property.area.between(number - delta, number + delta))
        if _model_has_column("kitchen_area", available_fields):
            conditions.append(Property.kitchen_area.between(number - delta, number + delta))

        if number == int(number):
            int_number = int(number)
            if _model_has_column("floor", available_fields) and 1 <= int_number <= 200:
                conditions.append(Property.floor == int_number)
            if _model_has_column("building_floors", available_fields) and 1 <= int_number <= 200:
                conditions.append(Property.building_floors == int_number)
            if _model_has_column("building_year", available_fields):
                current_year = datetime.now(tz=timezone.utc).year
                if 1900 <= int_number <= current_year + 1:
                    conditions.append(Property.building_year == int_number)

        price_value = parse_money_to_tenge(query_text)
        if price_value is not None and should_search_price(query_text) and _model_has_column("price", available_fields):
            tolerance = max(price_value * Decimal("0.01"), Decimal("100000"))
            conditions.append(Property.price.between(price_value - tolerance, price_value + tolerance))

    search_id = _extract_id_from_search(query_text)
    if search_id is not None:
        conditions.append(Property.id == search_id)

    return conditions
