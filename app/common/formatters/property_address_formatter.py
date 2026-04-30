from __future__ import annotations

import re

_SEPARATORS_RE = re.compile(r"\s*,\s*")
_SPACES_RE = re.compile(r"\s+")
_DUPLICATE_COMMAS_RE = re.compile(r",+")
_HOUSE_TOKEN_RE = re.compile(r"^(?:д(?:ом)?\.?\s*)?(\d+[\w/-]*)$", re.IGNORECASE)
_STREET_WITH_HOUSE_RE = re.compile(
    r"^(?:ул(?:ица)?\.?\s+)?(?P<street>[\w\-А-Яа-яЁёІіҢңҒғҚқҮүҰұӨөҺһ ]+?)\s+(?P<house>\d+[\w/-]*)$",
    re.IGNORECASE,
)



def _clean_text(value: str) -> str:
    compact = _SPACES_RE.sub(" ", value.replace(";", ",").strip())
    compact = _DUPLICATE_COMMAS_RE.sub(",", compact)
    compact = _SEPARATORS_RE.sub(", ", compact)
    return compact.strip(" ,")



def _strip_district_tokens(address: str, district: str) -> str:
    if not district:
        return address

    district_pattern = re.escape(district.strip())
    pattern = re.compile(
        rf"\b(?:мкр\.?|микрорайон|район)?\s*{district_pattern}\b",
        re.IGNORECASE,
    )
    cleaned = pattern.sub(" ", address)
    return _clean_text(cleaned)



def _extract_house_number(address: str) -> str | None:
    normalized = _clean_text(address)
    pieces = [p.strip() for p in normalized.split(",") if p.strip()]
    for piece in reversed(pieces):
        m = _HOUSE_TOKEN_RE.match(piece)
        if m:
            return m.group(1)

    direct = re.search(r"\b(?:д(?:ом)?\.?\s*)(\d+[\w/-]*)\b", normalized, re.IGNORECASE)
    if direct:
        return direct.group(1)

    trailing = re.search(r"(\d+[\w/-]*)$", normalized)
    if trailing:
        return trailing.group(1)
    return None



def format_property_address_for_display(district: str | None, address: str | None) -> str:
    if not address or not str(address).strip():
        return "-"

    cleaned = _clean_text(str(address))
    district_value = (district or "").strip()
    without_district = _strip_district_tokens(cleaned, district_value)

    house_number = _extract_house_number(without_district)

    if not without_district and house_number:
        return f"д{house_number}"

    street_match = _STREET_WITH_HOUSE_RE.match(without_district)
    if street_match:
        street = _clean_text(street_match.group("street"))
        return f"ул. {street}, д{street_match.group('house')}"

    only_house = _HOUSE_TOKEN_RE.match(without_district)
    if only_house:
        return f"д{only_house.group(1)}"

    if house_number and re.search(r"\bулица\b|\bул\.?\b", without_district, re.IGNORECASE):
        street = re.sub(r"\bулица\b|\bул\.?\b", "", without_district, flags=re.IGNORECASE)
        street = re.sub(r"\b(?:д(?:ом)?\.?)\s*\d+[\w/-]*\b", "", street, flags=re.IGNORECASE)
        street = _clean_text(street)
        if street:
            return f"ул. {street}, д{house_number}"

    return without_district or cleaned
