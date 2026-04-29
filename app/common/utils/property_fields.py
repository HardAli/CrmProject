from __future__ import annotations

import re
from datetime import datetime, timezone


ALLOWED_BUILDING_MATERIALS = {"Кирпич", "Панель", "Монолит"}


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
