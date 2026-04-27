from __future__ import annotations

from decimal import Decimal
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.clients import DISTRICT_OPTIONS
from app.bot.keyboards.properties import PROPERTY_TYPE_OPTIONS, PROPERTY_TYPE_MAP, get_properties_list_inline_keyboard
from app.common.enums import PropertyStatus
from app.services.object_filters import PRICE_PRESETS_MLN

OBJ_FILTER_PREFIX = "objflt"

PROPERTY_TYPE_VALUE_BY_LABEL = {label: enum_value.value for label, enum_value in PROPERTY_TYPE_MAP.items()}


def _selected(value: bool, label: str) -> str:
    return f"✅ {label}" if value else label


def build_objects_list_keyboard(objects: list[Any], filters: dict[str, Any], page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = get_properties_list_inline_keyboard(objects).inline_keyboard
    rows.extend(
        [
            [
                InlineKeyboardButton(text="🔎 Поиск", callback_data=f"{OBJ_FILTER_PREFIX}:search"),
                InlineKeyboardButton(text="⚙️ Фильтры", callback_data=f"{OBJ_FILTER_PREFIX}:menu"),
            ],
            [
                InlineKeyboardButton(text="↕️ Сортировка", callback_data=f"{OBJ_FILTER_PREFIX}:sortmenu"),
                InlineKeyboardButton(text="🧹 Сброс", callback_data=f"{OBJ_FILTER_PREFIX}:reset"),
            ],
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"{OBJ_FILTER_PREFIX}:page:{max(1, page - 1)}"),
                InlineKeyboardButton(text=f"{page}/{max(total_pages, 1)}", callback_data=f"{OBJ_FILTER_PREFIX}:noop"),
                InlineKeyboardButton(text="➡️", callback_data=f"{OBJ_FILTER_PREFIX}:page:{min(total_pages, page + 1)}"),
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_filters_menu_keyboard(filters: dict[str, Any], *, available_fields: set[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Тип", callback_data=f"{OBJ_FILTER_PREFIX}:type")],
        [
            InlineKeyboardButton(text="Комнаты", callback_data=f"{OBJ_FILTER_PREFIX}:rooms"),
            InlineKeyboardButton(text="Цена", callback_data=f"{OBJ_FILTER_PREFIX}:price"),
        ],
        [
            InlineKeyboardButton(text="Район", callback_data=f"{OBJ_FILTER_PREFIX}:district"),
            InlineKeyboardButton(text="Площадь", callback_data=f"{OBJ_FILTER_PREFIX}:area"),
        ],
        [
            InlineKeyboardButton(text="Этаж", callback_data=f"{OBJ_FILTER_PREFIX}:floor"),
            InlineKeyboardButton(text="Статус", callback_data=f"{OBJ_FILTER_PREFIX}:status"),
        ],
        [InlineKeyboardButton(text="Дата", callback_data=f"{OBJ_FILTER_PREFIX}:date")],
    ]

    if "building_material" in available_fields:
        rows.append([InlineKeyboardButton(text="Дом", callback_data=f"{OBJ_FILTER_PREFIX}:material")])
    if "condition" in available_fields:
        rows.append([InlineKeyboardButton(text="Состояние", callback_data=f"{OBJ_FILTER_PREFIX}:condition")])
    if "mortgage_available" in available_fields:
        rows.append([InlineKeyboardButton(text="Ипотека", callback_data=f"{OBJ_FILTER_PREFIX}:mortgage")])
    if "building_year" in available_fields:
        rows.append([InlineKeyboardButton(text="Год", callback_data=f"{OBJ_FILTER_PREFIX}:year")])

    rows.extend(
        [
            [InlineKeyboardButton(text="✅ Показать объекты", callback_data=f"{OBJ_FILTER_PREFIX}:show")],
            [
                InlineKeyboardButton(text="🧹 Сбросить", callback_data=f"{OBJ_FILTER_PREFIX}:reset"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{OBJ_FILTER_PREFIX}:show"),
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_rooms_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    selected = {str(value) for value in filters.get("rooms", [])}
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_selected("1" in selected, "1-х"), callback_data=f"{OBJ_FILTER_PREFIX}:room:1"),
                InlineKeyboardButton(text=_selected("2" in selected, "2-х"), callback_data=f"{OBJ_FILTER_PREFIX}:room:2"),
                InlineKeyboardButton(text=_selected("3" in selected, "3-х"), callback_data=f"{OBJ_FILTER_PREFIX}:room:3"),
            ],
            [
                InlineKeyboardButton(text=_selected("4" in selected, "4-х"), callback_data=f"{OBJ_FILTER_PREFIX}:room:4"),
                InlineKeyboardButton(text=_selected("5+" in selected, "5+"), callback_data=f"{OBJ_FILTER_PREFIX}:room:5+"),
            ],
            [InlineKeyboardButton(text="Любая", callback_data=f"{OBJ_FILTER_PREFIX}:rooms:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )


def build_price_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    selected_max = filters.get("price_max")
    rows: list[list[InlineKeyboardButton]] = []
    line: list[InlineKeyboardButton] = []
    for preset in PRICE_PRESETS_MLN:
        value = preset * 1_000_000
        label = _selected(selected_max == Decimal(value) and filters.get("price_min") is None, f"До {preset}")
        line.append(InlineKeyboardButton(text=label, callback_data=f"{OBJ_FILTER_PREFIX}:price:max:{preset}"))
        if len(line) == 3:
            rows.append(line)
            line = []
    if line:
        rows.append(line)

    rows.extend(
        [
            [InlineKeyboardButton(text="От и до", callback_data=f"{OBJ_FILTER_PREFIX}:price:manual")],
            [InlineKeyboardButton(text="Любая", callback_data=f"{OBJ_FILTER_PREFIX}:price:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_district_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    selected = set(filters.get("districts", []))
    rows: list[list[InlineKeyboardButton]] = []
    line: list[InlineKeyboardButton] = []
    for district in DISTRICT_OPTIONS[:12]:
        line.append(
            InlineKeyboardButton(
                text=_selected(district in selected, district),
                callback_data=f"{OBJ_FILTER_PREFIX}:district:set:{district}",
            )
        )
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)

    rows.extend(
        [
            [InlineKeyboardButton(text="Любой", callback_data=f"{OBJ_FILTER_PREFIX}:district:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_floor_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    floor_mode = filters.get("floor_mode")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_selected(floor_mode == "not_first", "Не первый"), callback_data=f"{OBJ_FILTER_PREFIX}:floor:not_first")],
            [InlineKeyboardButton(text=_selected(floor_mode == "not_last", "Не последний"), callback_data=f"{OBJ_FILTER_PREFIX}:floor:not_last")],
            [InlineKeyboardButton(text=_selected(floor_mode == "not_first_not_last", "Не 1/посл"), callback_data=f"{OBJ_FILTER_PREFIX}:floor:not_first_not_last")],
            [
                InlineKeyboardButton(text=_selected(floor_mode == "first", "1 этаж"), callback_data=f"{OBJ_FILTER_PREFIX}:floor:first"),
                InlineKeyboardButton(text=_selected(floor_mode == "last", "Последний"), callback_data=f"{OBJ_FILTER_PREFIX}:floor:last"),
            ],
            [InlineKeyboardButton(text=_selected(floor_mode == "2_4", "2-4 этаж"), callback_data=f"{OBJ_FILTER_PREFIX}:floor:2_4")],
            [InlineKeyboardButton(text="Любой", callback_data=f"{OBJ_FILTER_PREFIX}:floor:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )


def build_sort_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    current_sort = filters.get("sort", "newest")
    options = [
        ("newest", "Сначала новые"),
        ("price_asc", "Сначала дешевые"),
        ("price_desc", "Сначала дорогие"),
        ("area_desc", "Больше площадь"),
        ("area_asc", "Меньше площадь"),
        ("price_per_m2", "Цена за м²"),
    ]
    rows = [
        [
            InlineKeyboardButton(
                text=_selected(current_sort == key, title),
                callback_data=f"{OBJ_FILTER_PREFIX}:sort:{key}",
            )
        ]
        for key, title in options
    ]
    rows.append([InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:show")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_type_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    current_type = filters.get("property_type")
    rows = [
        [
            InlineKeyboardButton(
                text=_selected(current_type == PROPERTY_TYPE_VALUE_BY_LABEL[label], label),
                callback_data=f"{OBJ_FILTER_PREFIX}:type:set:{PROPERTY_TYPE_VALUE_BY_LABEL[label]}",
            )
        ]
        for label in PROPERTY_TYPE_OPTIONS
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="Любой", callback_data=f"{OBJ_FILTER_PREFIX}:type:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_area_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    area_min = filters.get("area_min")
    area_max = filters.get("area_max")

    def is_selected(v_min: float | None, v_max: float | None) -> bool:
        normalized_min = None if v_min is None else Decimal(str(v_min))
        normalized_max = None if v_max is None else Decimal(str(v_max))
        return area_min == normalized_min and area_max == normalized_max

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_selected(is_selected(None, 40), "До 40"), callback_data=f"{OBJ_FILTER_PREFIX}:area:set:upto_40"),
                InlineKeyboardButton(text=_selected(is_selected(40, 50), "40-50"), callback_data=f"{OBJ_FILTER_PREFIX}:area:set:40_50"),
            ],
            [
                InlineKeyboardButton(text=_selected(is_selected(50, 60), "50-60"), callback_data=f"{OBJ_FILTER_PREFIX}:area:set:50_60"),
                InlineKeyboardButton(text=_selected(is_selected(60, 80), "60-80"), callback_data=f"{OBJ_FILTER_PREFIX}:area:set:60_80"),
            ],
            [
                InlineKeyboardButton(text=_selected(is_selected(80, 100), "80-100"), callback_data=f"{OBJ_FILTER_PREFIX}:area:set:80_100"),
                InlineKeyboardButton(text=_selected(is_selected(100, None), "100+"), callback_data=f"{OBJ_FILTER_PREFIX}:area:set:100_plus"),
            ],
            [InlineKeyboardButton(text="Ввести вручную", callback_data=f"{OBJ_FILTER_PREFIX}:area:manual")],
            [InlineKeyboardButton(text="Любая", callback_data=f"{OBJ_FILTER_PREFIX}:area:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )


def build_date_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    mode = filters.get("created_date_mode")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_selected(mode == "today", "Сегодня"), callback_data=f"{OBJ_FILTER_PREFIX}:date:today")],
            [InlineKeyboardButton(text=_selected(mode == "3d", "За 3 дня"), callback_data=f"{OBJ_FILTER_PREFIX}:date:3d")],
            [InlineKeyboardButton(text=_selected(mode == "7d", "За неделю"), callback_data=f"{OBJ_FILTER_PREFIX}:date:7d")],
            [InlineKeyboardButton(text=_selected(mode == "30d", "За месяц"), callback_data=f"{OBJ_FILTER_PREFIX}:date:30d")],
            [InlineKeyboardButton(text="Все", callback_data=f"{OBJ_FILTER_PREFIX}:date:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )


def build_status_filter_keyboard(filters: dict[str, Any]) -> InlineKeyboardMarkup:
    selected = set(filters.get("status", []))
    options = [
        (PropertyStatus.ACTIVE.value, "Активные"),
        (PropertyStatus.RESERVED.value, "Забронированные"),
        (PropertyStatus.SOLD.value, "Проданные"),
        (PropertyStatus.ARCHIVED.value, "Архив"),
    ]
    rows = [
        [InlineKeyboardButton(text=_selected(value in selected, label), callback_data=f"{OBJ_FILTER_PREFIX}:status:set:{value}")]
        for value, label in options
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="Все", callback_data=f"{OBJ_FILTER_PREFIX}:status:any")],
            [InlineKeyboardButton(text="Готово", callback_data=f"{OBJ_FILTER_PREFIX}:menu")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
