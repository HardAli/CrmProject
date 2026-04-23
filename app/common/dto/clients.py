from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.common.enums import PropertyType, RequestType, WallMateria


@dataclass(slots=True)
class CreateClientDTO:
    full_name: str
    phone: str
    source: str | None
    request_type: RequestType
    property_type: PropertyType
    district: str | None
    rooms: str | None
    budget: Decimal | None
    floor: int | None
    building_floors: int | None
    wall_material: WallMaterial | None
    year_built: int | None
    note: str | None
    next_contact_at: datetime | None
    manager_id: int