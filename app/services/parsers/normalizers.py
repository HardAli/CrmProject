from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.bot.keyboards.properties import DISTRICT_OPTIONS_FOR_PROPERTY
from app.common.enums import PropertyStatus, PropertyType
from app.common.utils.phone_links import normalize_owner_phone
from app.schemas.parsed_property import ParsedPropertyData, RawParsedPropertyData

DISTRICT_CANONICAL = {item.lower(): item for item in DISTRICT_OPTIONS_FOR_PROPERTY}


def _normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized or None


def _extract_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9,\.]+", "", value).replace(",", ".")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _normalize_rooms(value: str | None) -> int | None:
    if not value:
        return None
    raw = value.strip().lower()
    if "студ" in raw or "studio" in raw:
        return None
    digits = re.search(r"\d+", raw)
    return int(digits.group(0)) if digits else None


def _normalize_property_type(title: str | None, description: str | None) -> PropertyType | None:
    basis = f"{title or ''} {description or ''}".lower()
    if any(word in basis for word in ("квартир", "апартамент", "студ")):
        return PropertyType.APARTMENT
    if "дом" in basis:
        return PropertyType.HOUSE
    if any(word in basis for word in ("коммер", "офис", "магазин")):
        return PropertyType.COMMERCIAL
    if any(word in basis for word in ("участ", "земл")):
        return PropertyType.LAND
    return None


def _extract_floor_pair(value: str | None) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    pair = re.search(r"(\d+)\s*/\s*(\d+)", value)
    if pair:
        return int(pair.group(1)), int(pair.group(2))
    pair = re.search(r"этаж\s*(\d+)\s*из\s*(\d+)", value.lower())
    if pair:
        return int(pair.group(1)), int(pair.group(2))
    return None, None


def normalize_parsed_data(raw_data: RawParsedPropertyData) -> ParsedPropertyData:
    regex_data = raw_data.payload.get("regex", {}) if isinstance(raw_data.payload, dict) else {}
    if not isinstance(regex_data, dict):
        regex_data = {}

    title = _normalize_text(str(regex_data.get("title", "")))
    description = _normalize_text(str(regex_data.get("description", "")))
    property_type = _normalize_property_type(title=title, description=description)

    district = _normalize_text(str(regex_data.get("district", "")))
    if district:
        district = DISTRICT_CANONICAL.get(district.lower(), district)

    address = _normalize_text(str(regex_data.get("address", "")))
    price = _extract_decimal(str(regex_data.get("price", "")))
    area = _extract_decimal(str(regex_data.get("area", "")))
    rooms = _normalize_rooms(str(regex_data.get("rooms", "")))

    floor, building_floors = _extract_floor_pair(str(regex_data.get("floor_pair", "")))

    owner_phone = _normalize_text(str(regex_data.get("owner_phone", "")))
    owner_phone_normalized = None
    warnings = list(raw_data.parse_warnings)
    if owner_phone:
        try:
            owner_phone_normalized = normalize_owner_phone(owner_phone)
            owner_phone = owner_phone_normalized
        except ValueError:
            warnings.append("Failed to normalize owner phone")
            owner_phone_normalized = None

    if floor is not None and building_floors is not None and floor > building_floors:
        warnings.append("Floor is greater than building floors; manual correction required")

    image_urls: list[str] = []
    image_block = regex_data.get("image_urls")
    if isinstance(image_block, str):
        image_urls = re.findall(r'https?://[^"\']+', image_block)

    return ParsedPropertyData(
        source=raw_data.source,
        source_url=raw_data.source_url,
        source_listing_id=raw_data.source_listing_id,
        title=title,
        property_type=property_type,
        district=district,
        address=address,
        owner_phone=owner_phone,
        owner_phone_normalized=owner_phone_normalized,
        price=price,
        area=area,
        rooms=rooms,
        floor=floor,
        building_floors=building_floors,
        description=description,
        status=PropertyStatus.ACTIVE,
        image_urls=image_urls,
        raw_data_json=raw_data.payload,
        parse_warnings=warnings,
    )
