from __future__ import annotations

import re
from datetime import datetime, timezone

from app.common.utils.value_parsers import parse_int_or_none


ALLOWED_BUILDING_MATERIALS = {"Кирпич", "Панель", "Монолит"}
MAX_PROPERTY_ROOMS = 50
MORE_THAN_FIVE_ROOMS_VALUE = 6


def parse_property_rooms_or_none(value: object) -> int | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    normalized = " ".join(text.lower().replace("ё", "е").split())
    compact = normalized.replace(" ", "")

    if normalized in {"студия", "неизвестно", "не указано", "пропустить"} or compact in {"?", "-", "unknown"}:
        return None

    if (
        normalized in {"больше 5", "более 5", "свыше 5"}
        or re.search(r"(?:больше|более|свыше)\s*5", normalized)
        or re.search(r"от\s*6", normalized)
        or compact in {"5+", ">5", "больше5", "более5", "свыше5", "от6", "6+"}
    ):
        return MORE_THAN_FIVE_ROOMS_VALUE

    parsed = parse_int_or_none(text)
    if parsed is not None and 0 < parsed <= MAX_PROPERTY_ROOMS:
        return parsed

    raise ValueError("Комнаты: выберите «Неизвестно», «Больше 5» или введите число от 1 до 50.")


def normalize_building_material(raw_value: object) -> str | None:
    if raw_value is None:
        return None

    text = str(raw_value).strip()
    if not text or len(text) > 50:
        return None

    lowered = text.lower()
    if "<" in text or ">" in text or "</" in lowered or "http" in lowered:
        return None

    mapping = {
        "кирпич": "Кирпич",
        "кирпичный": "Кирпич",
        "кирпичная": "Кирпич",
        "панель": "Панель",
        "панельный": "Панель",
        "панельная": "Панель",
        "панелька": "Панель",
        "монолит": "Монолит",
        "монолитный": "Монолит",
        "монолитная": "Монолит",
    }

    for key, normalized in mapping.items():
        if key in lowered:
            return normalized

    return text if text in ALLOWED_BUILDING_MATERIALS else None


def parse_building_year_or_none(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"(19|20)\d{2}", text)
    if not match:
        return None
    year = int(match.group(0))
    return year if is_valid_building_year(year) else None


def is_valid_building_year(year: int) -> bool:
    current_year = datetime.now(tz=timezone.utc).year
    return 1900 <= year <= current_year + 1


def extract_building_year(text: str | None) -> int | None:
    if not text:
        return None

    patterns = [
        r"(?:год постройки|г\.п\.|гп|постройки|дом)\D{0,20}((?:19|20)\d{2})",
        r"((?:19|20)\d{2})\s*(?:г\.п\.|гп|года|год|г\.)",
        r"((?:19|20)\d{2})",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, str(text), flags=re.IGNORECASE)
        for match in matches:
            year = int(match)
            if is_valid_building_year(year):
                return year
    return None


def extract_building_material(text: str | None) -> str | None:
    if not text:
        return None

    source = str(text)
    patterns = [
        r"(?:материал\s*стен|тип\s*дома|тип\s*строения)\D{0,20}(кирпич(?:ный|ная)?|панел(?:ь|ьный|ьная|ька)?|монолит(?:ный|ная)?)",
        r"\b(кирпич(?:ный|ная)?|панел(?:ь|ьный|ьная|ька)?|монолит(?:ный|ная)?)\b",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, source, flags=re.IGNORECASE)
        for match in matches:
            normalized = normalize_building_material(match)
            if normalized is not None:
                return normalized

    return None
