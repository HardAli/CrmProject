from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, case

from app.common.enums import PropertyStatus
from app.database.models.property import Property

ObjectFilters = dict[str, Any]

PRICE_PRESETS_MLN: tuple[int, ...] = (15, 20, 25, 30, 40, 50)
AREA_PRESETS: dict[str, tuple[Decimal | None, Decimal | None]] = {
    "upto_40": (None, Decimal("40")),
    "40_50": (Decimal("40"), Decimal("50")),
    "50_60": (Decimal("50"), Decimal("60")),
    "60_80": (Decimal("60"), Decimal("80")),
    "80_100": (Decimal("80"), Decimal("100")),
    "100_plus": (Decimal("100"), None),
}
FLOOR_MODES: set[str] = {
    "not_first",
    "not_last",
    "not_first_not_last",
    "first",
    "last",
    "2_4",
}
DATE_MODES_DAYS: dict[str, int] = {
    "today": 1,
    "3d": 3,
    "7d": 7,
    "30d": 30,
}


def get_default_object_filters() -> ObjectFilters:
    return {
        "property_type": None,
        "rooms": [],
        "price_min": None,
        "price_max": None,
        "districts": [],
        "area_min": None,
        "area_max": None,
        "floor_mode": None,
        "materials": [],
        "building_year_min": None,
        "conditions": [],
        "mortgage_available": None,
        "status": [PropertyStatus.ACTIVE.value],
        "created_date_mode": None,
        "sort": "newest",
        "page": 1,
    }


def reset_object_filters() -> ObjectFilters:
    return get_default_object_filters()


def update_object_filter(filters: ObjectFilters, key: str, value: Any, *, reset_page: bool = True) -> ObjectFilters:
    next_filters = deepcopy(filters)
    next_filters[key] = value
    if reset_page and key != "page":
        next_filters["page"] = 1
    return next_filters


def _coerce_statuses(statuses: list[str]) -> list[PropertyStatus]:
    normalized: list[PropertyStatus] = []
    for status in statuses:
        try:
            normalized.append(PropertyStatus(status))
        except ValueError:
            continue
    return normalized


def apply_object_filters(
    query: Select[tuple[Property]],
    filters: ObjectFilters,
    *,
    available_fields: set[str],
) -> Select[tuple[Property]]:
    if "status" in available_fields and filters.get("status"):
        statuses = _coerce_statuses(filters["status"])
        if statuses:
            query = query.where(Property.status.in_(statuses))

    if "property_type" in available_fields and filters.get("property_type"):
        query = query.where(Property.property_type == filters["property_type"])

    if "rooms" in available_fields and filters.get("rooms"):
        room_values = [str(value) for value in filters["rooms"]]
        query = query.where(Property.rooms.in_(room_values))

    if "price" in available_fields and filters.get("price_min") is not None:
        query = query.where(Property.price >= filters["price_min"])
    if "price" in available_fields and filters.get("price_max") is not None:
        query = query.where(Property.price <= filters["price_max"])

    if "district" in available_fields and filters.get("districts"):
        query = query.where(Property.district.in_(filters["districts"]))

    if "area" in available_fields and filters.get("area_min") is not None:
        query = query.where(Property.area >= filters["area_min"])
    if "area" in available_fields and filters.get("area_max") is not None:
        query = query.where(Property.area <= filters["area_max"])

    if {"floor", "building_floors"}.issubset(available_fields):
        floor_mode = filters.get("floor_mode")
        if floor_mode == "not_first":
            query = query.where(Property.floor > 1)
        elif floor_mode == "not_last":
            query = query.where(Property.floor < Property.building_floors)
        elif floor_mode == "not_first_not_last":
            query = query.where(and_(Property.floor > 1, Property.floor < Property.building_floors))
        elif floor_mode == "first":
            query = query.where(Property.floor == 1)
        elif floor_mode == "last":
            query = query.where(Property.floor == Property.building_floors)
        elif floor_mode == "2_4":
            query = query.where(Property.floor.between(2, 4))

    if "building_material" in available_fields and filters.get("materials"):
        query = query.where(Property.building_material.in_(filters["materials"]))

    if "building_year" in available_fields and filters.get("building_year_min") is not None:
        query = query.where(Property.building_year >= filters["building_year_min"])

    if "condition" in available_fields and filters.get("conditions"):
        query = query.where(Property.condition.in_(filters["conditions"]))

    if "mortgage_available" in available_fields and filters.get("mortgage_available") is not None:
        query = query.where(Property.mortgage_available.is_(filters["mortgage_available"]))

    if "created_at" in available_fields and filters.get("created_date_mode") in DATE_MODES_DAYS:
        days = DATE_MODES_DAYS[filters["created_date_mode"]]
        boundary = datetime.now(tz=timezone.utc) - timedelta(days=days)
        query = query.where(Property.created_at >= boundary)

    sort_mode = filters.get("sort") or "newest"
    if sort_mode == "price_asc" and "price" in available_fields:
        query = query.order_by(Property.price.asc(), Property.created_at.desc())
    elif sort_mode == "price_desc" and "price" in available_fields:
        query = query.order_by(Property.price.desc(), Property.created_at.desc())
    elif sort_mode == "area_desc" and "area" in available_fields:
        query = query.order_by(Property.area.desc().nullslast(), Property.created_at.desc())
    elif sort_mode == "area_asc" and "area" in available_fields:
        query = query.order_by(Property.area.asc().nullslast(), Property.created_at.desc())
    elif sort_mode == "price_per_m2" and {"price", "area"}.issubset(available_fields):
        price_per_m2 = case((Property.area.is_(None), None), (Property.area == 0, None), else_=Property.price / Property.area)
        query = query.order_by(price_per_m2.asc().nullslast(), Property.created_at.desc())
    else:
        query = query.order_by(Property.created_at.desc())

    return query
