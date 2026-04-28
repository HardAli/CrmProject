from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.common.enums import PropertyType
from app.common.formatters.property_formatter import format_object_compact
from app.common.utils.formatters import format_decimal_plain
from app.database.models.property import Property

SORT_LABELS: dict[str, str] = {
    "newest": "сначала новые",
    "price_asc": "сначала дешевые",
    "price_desc": "сначала дорогие",
    "area_desc": "больше площадь",
    "area_asc": "меньше площадь",
    "price_per_m2": "цена за м²",
}

PROPERTY_TYPE_LABELS: dict[str, str] = {
    PropertyType.APARTMENT.value: "квартира",
    PropertyType.HOUSE.value: "дом",
    PropertyType.COMMERCIAL.value: "коммерция",
    PropertyType.LAND.value: "участок",
}

FLOOR_LABELS: dict[str, str] = {
    "not_first": "не первый",
    "not_last": "не последний",
    "not_first_not_last": "не 1/посл",
    "first": "1 этаж",
    "last": "последний",
    "2_4": "2-4 этаж",
}

DATE_MODE_LABELS: dict[str, str] = {
    "today": "сегодня",
    "3d": "за 3 дня",
    "7d": "за неделю",
    "30d": "за месяц",
}

STATUS_LABELS: dict[str, str] = {
    "active": "активные",
    "reserved": "забронированные",
    "sold": "проданные",
    "archived": "архив",
}


def _fmt_mln(value: Decimal | None) -> str:
    if value is None:
        return ""
    mln = (value / Decimal("1000000")).quantize(Decimal("0.1"))
    return format_decimal_plain(mln, max_fraction_digits=1)


def build_object_filters_summary(filters: dict[str, Any]) -> str:
    parts: list[str] = []

    if filters.get("property_type"):
        parts.append(PROPERTY_TYPE_LABELS.get(filters["property_type"], str(filters["property_type"])))

    if filters.get("rooms"):
        rooms = sorted(str(room) for room in filters["rooms"])
        parts.append(f"{','.join(rooms)}х")

    price_min = filters.get("price_min")
    price_max = filters.get("price_max")
    if price_min is not None and price_max is not None:
        parts.append(f"{_fmt_mln(price_min)}-{_fmt_mln(price_max)}")
    elif price_max is not None:
        parts.append(f"до {_fmt_mln(price_max)}")
    elif price_min is not None:
        parts.append(f"от {_fmt_mln(price_min)}")

    if filters.get("districts"):
        parts.append(",".join(filters["districts"]))

    area_min = filters.get("area_min")
    area_max = filters.get("area_max")
    if area_min is not None and area_max is not None:
        parts.append(f"{area_min}-{area_max}м²")
    elif area_max is not None:
        parts.append(f"до {area_max}м²")
    elif area_min is not None:
        parts.append(f"от {area_min}м²")

    if filters.get("floor_mode"):
        parts.append(FLOOR_LABELS.get(filters["floor_mode"], str(filters["floor_mode"])))

    if filters.get("created_date_mode"):
        parts.append(DATE_MODE_LABELS.get(filters["created_date_mode"], str(filters["created_date_mode"])))

    statuses = filters.get("status") or []
    if statuses and statuses != ["active"]:
        parts.append("/".join(STATUS_LABELS.get(status, status) for status in statuses))

    return "|".join(parts) if parts else "нет"


def build_objects_list_text(
    objects: list[Property],
    filters: dict[str, Any],
    total_count: int,
    page: int,
    per_page: int,
) -> str:
    summary = build_object_filters_summary(filters)
    rows = ["<b>База объектов</b>", "", f"Фильтр: {summary}", f"Найдено: {total_count}", ""]
    start_index = (page - 1) * per_page + 1

    if not objects:
        rows.append("Объекты не найдены по выбранным фильтрам.")
    else:
        for idx, obj in enumerate(objects, start=start_index):
            rows.append(f"{idx}. {format_object_compact(obj, with_status=False)}")

    return "\n".join(rows)


def build_filters_menu_text(filters: dict[str, Any], *, available_fields: set[str]) -> str:
    lines = ["<b>Фильтры объектов</b>", ""]
    lines.append(f"Тип: {PROPERTY_TYPE_LABELS.get(filters.get('property_type'), 'любой')}")
    lines.append(f"Комн.: {', '.join(str(v) for v in filters.get('rooms', [])) or 'любая'}")

    price_min = filters.get("price_min")
    price_max = filters.get("price_max")
    if price_min is None and price_max is None:
        lines.append("Цена: любая")
    elif price_min is not None and price_max is not None:
        lines.append(f"Цена: {_fmt_mln(price_min)}-{_fmt_mln(price_max)} млн")
    elif price_max is not None:
        lines.append(f"Цена: до {_fmt_mln(price_max)} млн")
    else:
        lines.append(f"Цена: от {_fmt_mln(price_min)} млн")

    lines.append(f"Район: {', '.join(filters.get('districts', [])) or 'любой'}")

    area_min = filters.get("area_min")
    area_max = filters.get("area_max")
    if area_min is None and area_max is None:
        lines.append("Площадь: любая")
    elif area_min is not None and area_max is not None:
        lines.append(f"Площадь: {area_min}-{area_max} м²")
    elif area_max is not None:
        lines.append(f"Площадь: до {area_max} м²")
    else:
        lines.append(f"Площадь: от {area_min} м²")

    lines.append(f"Этаж: {FLOOR_LABELS.get(filters.get('floor_mode'), 'любой')}")

    if "building_material" in available_fields:
        lines.append(f"Дом: {', '.join(filters.get('materials', [])) or 'любой'}")
    else:
        lines.append("Дом: недоступно")

    if "condition" in available_fields:
        lines.append(f"Состояние: {', '.join(filters.get('conditions', [])) or 'любое'}")
    else:
        lines.append("Состояние: недоступно")

    if "mortgage_available" in available_fields:
        mortgage = filters.get("mortgage_available")
        mortgage_label = "любая" if mortgage is None else ("проходит" if mortgage else "не проходит")
        lines.append(f"Ипотека: {mortgage_label}")
    else:
        lines.append("Ипотека: недоступно")

    lines.append(f"Дата: {DATE_MODE_LABELS.get(filters.get('created_date_mode'), 'все')}")
    lines.append(
        f"Статус: {', '.join(STATUS_LABELS.get(status, status) for status in filters.get('status', [])) or 'все'}"
    )
    lines.append(f"Сортировка: {SORT_LABELS.get(filters.get('sort', 'newest'), 'сначала новые')}")

    return "\n".join(lines)
