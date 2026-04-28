from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.common.enums import PropertyStatus, PropertyType


@dataclass(slots=True)
class CreatePropertyDTO:
    title: str
    property_type: PropertyType
    district: str
    address: str
    owner_phone: str
    price: Decimal
    area: Decimal
    status: PropertyStatus
    manager_id: int
    kitchen_area: Decimal | None = None
    rooms: int | None = None
    floor: int | None = None
    building_floors: int | None = None
    building_year: int | None = None
    building_material: str | None = None
    description: str | None = None
    link: str | None = None
