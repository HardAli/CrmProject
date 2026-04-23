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
    rooms: str | None
    floor: int | None
    building_floors: int | None
    description: str | None
    link: str | None
    status: PropertyStatus
    manager_id: int