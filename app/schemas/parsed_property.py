from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.common.enums import PropertyStatus, PropertyType


@dataclass(slots=True)
class RawParsedPropertyData:
    source: str
    source_url: str
    source_listing_id: str | None = None
    payload: dict[str, object] = field(default_factory=dict)
    html_text: str | None = None
    parse_warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedPropertyData:
    source: str
    source_url: str
    source_listing_id: str | None = None
    title: str | None = None
    property_type: PropertyType | None = None
    district: str | None = None
    address: str | None = None
    owner_phone: str | None = None
    owner_phone_normalized: str | None = None
    price: Decimal | None = None
    area: Decimal | None = None
    rooms: int | None = None
    floor: int | None = None
    building_floors: int | None = None
    building_year: int | None = None
    building_material: str | None = None
    description: str | None = None
    status: PropertyStatus = PropertyStatus.ACTIVE
    image_urls: list[str] = field(default_factory=list)
    raw_data_json: dict[str, object] | None = None
    parse_warnings: list[str] = field(default_factory=list)
    missing_required_fields: list[str] = field(default_factory=list)

    @property
    def is_complete_for_create(self) -> bool:
        return len(self.missing_required_fields) == 0
