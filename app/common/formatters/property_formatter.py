from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from html import escape

from app.common.enums import PropertyStatus, PropertyType
from app.common.formatters.property_address_formatter import format_property_address_for_display
from app.common.utils.formatters import format_area, format_area_compact, format_decimal_plain
from app.common.utils.phone_links import format_owner_phone, format_phone_for_display
from app.database.models.property import Property

EMPTY_SHORT = "—"
_HOUSE_NUMBER_RE = re.compile(r"(?:^|[\s,])д\.?\s*(\d+[\w/-]*)\b", re.IGNORECASE)

PROPERTY_TYPE_LABELS: dict[PropertyType, str] = {
    PropertyType.APARTMENT: "Квартира",
    PropertyType.HOUSE: "Дом",
    PropertyType.COMMERCIAL: "Коммерческая",
    PropertyType.LAND: "Участок",
}

PROPERTY_STATUS_LABELS: dict[PropertyStatus, str] = {
    PropertyStatus.ACTIVE: "Активен",
    PropertyStatus.RESERVED: "Забронирован",
    PropertyStatus.AGREED: "Договорились",
    PropertyStatus.NOT_REACHED: "Не дозвонился",
    PropertyStatus.REFUSED_TO_WORK: "Отказ. работать",
    PropertyStatus.SOLD: "Продан",
    PropertyStatus.ARCHIVED: "Архив",
    PropertyStatus.EXTERNAL_AGENCY: "Чуж.агенство",
}


def safe_html(value: object) -> str:
    if value is None:
        return "—"
    return escape(str(value), quote=False)


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def _format_money_for_share(value: Decimal | None) -> str:
    return _format_money(value).replace(" ", ".")


def _format_decimal(value: Decimal | None) -> str:
    return format_decimal_plain(value)


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def format_rooms_short(rooms: int | str | None, title: str | None = None) -> str:
    if rooms is not None:
        rooms_value = str(rooms).strip()
        if rooms_value:
            return f"{rooms_value}-х"
    if title:
        lowered = title.lower()
        for rooms_count in range(1, 6):
            if f"{rooms_count}-комнат" in lowered:
                return f"{rooms_count}-х"
    return "—"


def format_floor_short(floor: int | None, building_floors: int | None) -> str:
    if floor is None and building_floors is None:
        return "—"
    if floor is None:
        return f"—/{building_floors}"
    if building_floors is None:
        return f"{floor}/—"
    return f"{floor}/{building_floors}"


def format_price_mln(price: Decimal | None) -> str:
    if price is None:
        return "—"
    mln_value = (price / Decimal("1000000")).quantize(Decimal("0.1"))
    return f"{format_decimal_plain(mln_value, max_fraction_digits=1)} млн"


def format_price_compact(price: Decimal | None) -> str:
    if price is None:
        return "—"
    millions = price / Decimal("1000000")
    return format_decimal_plain(millions, max_fraction_digits=1)


CALL_RESULT_LABELS: dict[str, str] = {
    "AGREED": "Договорился",
    "NO_ANSWER": "Недозвон",
    "REJECTED": "Отказ",
    "SOLD": "Продано",
    "SKIPPED": "Пропуск",
}


def format_property_call_card(
    property_obj: Property,
    position: int | None = None,
    total: int | None = None,
    today_stats: dict[str, int] | None = None,
) -> str:
    today_stats = today_stats or {}
    phone_text = format_phone_for_display(property_obj.owner_phone)
    progress = ""
    if position is not None and total is not None:
        progress = f"{position}/{total}"
    elif position is not None:
        progress = str(position)

    short_row = "|".join(
        [
            format_rooms_short(property_obj.rooms, property_obj.title),
            format_area_compact(property_obj.area),
            format_floor_short(property_obj.floor, property_obj.building_floors),
            property_obj.district or "—",
            format_price_compact(property_obj.price),
        ]
    )

    building_row = "|".join(
        [
            property_obj.building_material or "—",
            safe_html(property_obj.building_year),
        ]
    )

    last_call_at = getattr(property_obj, "last_call_at", None)
    last_call_status = getattr(property_obj, "last_call_status", None)
    if last_call_at is None:
        last_line = "Последний: —"
    else:
        status_label = CALL_RESULT_LABELS.get(str(last_call_status), str(last_call_status or "—"))
        last_line = f"Последний: {last_call_at.strftime('%d.%m %H:%M')} — {status_label}"

    next_call_at = getattr(property_obj, "next_call_at", None)
    next_line = ""
    if next_call_at is not None:
        next_line = f"\nСледующий: {next_call_at.strftime('%d.%m %H:%M')}"

    prefix = f"{progress} | " if progress else ""
    return (
        "📞 Прозвон объектов\n\n"
        f"{prefix}Сегодня: ✅{today_stats.get('AGREED', 0)} 📵{today_stats.get('NO_ANSWER', 0)} ❌{today_stats.get('REJECTED', 0)}\n\n"
        f"🏠 {safe_html(short_row)}\n"
        f"🍳 Кухня: {safe_html(format_area_compact(property_obj.kitchen_area))}\n"
        f"🏢 {safe_html(building_row)}\n"
        f"📍 {safe_html(format_property_address_for_display(property_obj.district, property_obj.address))}\n"
        f"☎️ {safe_html(phone_text)}\n\n"
        f"Попыток: {safe_html(getattr(property_obj, 'call_attempts', 0) or 0)}\n"
        f"{safe_html(last_line)}{safe_html(next_line)}"
    )


def _trim_middle(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    if max_len <= 1:
        return value[:max_len]
    return f"{value[: max_len - 1]}…"


def trim_button_text(value: str, max_length: int | None = None) -> str:
    text = value.strip() or EMPTY_SHORT
    if max_length is None or len(text) <= max_length:
        return text
    if max_length <= 1:
        return text[:max_length]
    return f"{text[: max_length - 1]}…"


def format_button_compact_text(value: str, max_length: int | None = None) -> str:
    text = (value or "").strip() or "?"
    replacements = (
        ("млн", "м"),
        ("тыс", "т"),
        ("Любой", "?"),
        ("любой", "?"),
        ("люб.", "?"),
        ("Люб.", "?"),
        (EMPTY_SHORT, "?"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    text = text.replace(" ", "")
    return trim_button_text(text or "?", max_length)


def format_price_short(value: object) -> str:
    if value is None:
        return EMPTY_SHORT
    try:
        price = Decimal(str(value))
    except Exception:
        return trim_button_text(str(value), 12) if str(value).strip() else EMPTY_SHORT
    if price >= Decimal("1000000"):
        return f"{format_decimal_plain(price / Decimal('1000000'), max_fraction_digits=1)}млн"
    if price >= Decimal("1000"):
        return f"{format_decimal_plain(price / Decimal('1000'), max_fraction_digits=0)}тыс"
    return format_decimal_plain(price, max_fraction_digits=0)


def format_rooms_list_short(value: object) -> str:
    if value is None:
        return EMPTY_SHORT
    text = str(value).strip().lower()
    if not text:
        return EMPTY_SHORT
    if text in {"studio", "студия"} or "студ" in text:
        return "студия"
    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        return f"{digits}к"
    return trim_button_text(text, 8)


def format_rooms_range_short(values: list[str] | None) -> str:
    if not values:
        return EMPTY_SHORT
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    if not cleaned:
        return EMPTY_SHORT
    if any(value.lower() in {"studio", "студия"} or "студ" in value.lower() for value in cleaned):
        return "студия"
    numeric_values: list[int] = []
    for value in cleaned:
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            numeric_values.append(int(digits))
    if not numeric_values:
        return trim_button_text(",".join(cleaned), 10)
    unique_values = sorted(set(numeric_values))
    if len(unique_values) == 1:
        return f"{unique_values[0]}к"
    return f"{unique_values[0]}-{unique_values[-1]}к"


def format_area_short(value: object) -> str:
    text = format_area_compact(value)
    return text if text else EMPTY_SHORT


def format_area_range_short(area_min: object = None, area_max: object = None) -> str:
    if area_min is None and area_max is None:
        return EMPTY_SHORT
    if area_min is not None and area_max is not None:
        return f"{format_decimal_plain(area_min)}-{format_decimal_plain(area_max)}м²"
    if area_min is not None:
        return f"от {format_decimal_plain(area_min)}м²"
    return f"до {format_decimal_plain(area_max)}м²"


def format_floor_range_short(
    floor_min: int | None = None,
    floor_max: int | None = None,
    *,
    allow_first_floor: bool | None = None,
    allow_last_floor: bool | None = None,
    preferred_text: str | None = None,
) -> str:
    text = (preferred_text or "").strip().lower()
    if text:
        if "сред" in text:
            return "средн."
        if "не первый" in text and ("не послед" in text or "без послед" in text):
            return "не 1/посл"
        if "не первый" in text or "без 1" in text:
            return "не 1"
        if "не послед" in text or "без послед" in text:
            return "не посл"
        if text != "не важно":
            return trim_button_text(preferred_text or "", 12)
    if allow_first_floor is False and allow_last_floor is False:
        return "не 1/посл"
    if allow_first_floor is False:
        return "не 1"
    if allow_last_floor is False:
        return "не посл"
    if floor_min is not None and floor_max is not None:
        return f"{floor_min}-{floor_max}эт"
    if floor_min is not None:
        return f"от {floor_min}эт"
    if floor_max is not None:
        return f"до {floor_max}эт"
    return EMPTY_SHORT


def format_property_floor_short(floor: int | None, total_floors: int | None) -> str:
    if floor is None and total_floors is None:
        return EMPTY_SHORT
    if floor is None:
        return f"—/{total_floors}"
    if total_floors is None:
        return f"{floor}эт"
    return f"{floor}/{total_floors}"


def format_year_short(year_min: object = None, year_max: object = None, year: object = None) -> str:
    if year is not None:
        return str(year).strip() or EMPTY_SHORT
    if year_min is not None and year_max is not None:
        return f"{year_min}-{year_max}"
    if year_min is not None:
        return f"от {year_min}"
    if year_max is not None:
        return f"до {year_max}"
    return EMPTY_SHORT


def format_material_short(material: object) -> str:
    if material is None:
        return EMPTY_SHORT
    raw = getattr(material, "value", material)
    text = str(raw).strip().lower()
    if not text or text == "не важно":
        return EMPTY_SHORT
    known = (
        ("кирп", "кир"),
        ("brick", "кир"),
        ("панел", "пан"),
        ("panel", "пан"),
        ("монол", "мон"),
        ("monolith", "мон"),
        ("керамзит", "кер"),
        ("саман", "сам"),
        ("блок", "бло"),
        ("дерев", "дер"),
    )
    for needle, short in known:
        if needle in text:
            return short
    return text[:3] if len(text) > 3 else text


def format_property_type_short(property_type: object) -> str:
    value = getattr(property_type, "value", property_type)
    text = str(value or "").strip().lower()
    if not text:
        return EMPTY_SHORT
    mapping = {
        "apartment": "кв",
        "квартира": "кв",
        "house": "дм",
        "дом": "дм",
        "land": "уч",
        "участок": "уч",
        "commercial": "км",
        "коммерческая": "км",
        "коммерция": "км",
        "townhouse": "тх",
        "таунхаус": "тх",
        "cottage": "дч",
        "дача": "дч",
        "garage": "гр",
        "гараж": "гр",
    }
    return mapping.get(text, EMPTY_SHORT)


def format_districts_short(districts: list[str] | tuple[str, ...] | str | None, max_items: int = 2) -> str:
    if districts is None:
        return EMPTY_SHORT
    if isinstance(districts, str):
        values = [part.strip() for part in districts.split(",") if part.strip()]
    else:
        values = [str(value).strip() for value in districts if str(value).strip()]
    if not values:
        return EMPTY_SHORT
    visible = values[:max_items]
    suffix = f" +{len(values) - len(visible)}" if len(values) > len(visible) else ""
    return f"{', '.join(visible)}{suffix}"


def format_property_button_text(prop: Property, max_length: int | None = None) -> str:
    parts = [
        format_price_short(prop.price),
        format_rooms_list_short(prop.rooms),
        format_property_floor_short(prop.floor, prop.building_floors),
        prop.district or EMPTY_SHORT,
        format_area_short(prop.area),
        format_material_short(prop.building_material),
        format_year_short(year=prop.building_year),
        format_property_type_short(prop.property_type),
    ]
    return format_button_compact_text("|".join(parts), max_length)


def format_seller_list_button(prop: Property, max_length: int | None = None) -> str:
    return format_property_button_text(prop, max_length=max_length)


def format_object_compact(prop: Property, with_status: bool = True, max_length: int | None = None) -> str:
    status = format_property_status(prop)
    prefix_parts = [
        format_rooms_short(prop.rooms, prop.title),
        format_area_short(prop.area),
        format_floor_short(prop.floor, prop.building_floors),
    ]
    address = format_property_address_for_display(prop.district, prop.address) if prop.address else (prop.title or "—")
    district = prop.district or "—"
    suffix_parts = [format_price_mln(prop.price)]
    if with_status and prop.status != PropertyStatus.ACTIVE:
        suffix_parts.append(status)

    text = "|".join([*prefix_parts, address, district, *suffix_parts])
    if max_length is None or len(text) <= max_length:
        return text

    # Приоритетно сохраняем начало строки, цену и статус;
    # сокращаем адрес, затем район.
    min_len_without_address = len("|".join([*prefix_parts, "", district, *suffix_parts]))
    address_len_limit = max(max_length - (min_len_without_address + 1), 1)
    address = _trim_middle(address, address_len_limit)
    text = "|".join([*prefix_parts, address, district, *suffix_parts])
    if len(text) <= max_length:
        return text

    min_len_without_district = len("|".join([*prefix_parts, address, "", *suffix_parts]))
    district_len_limit = max(max_length - (min_len_without_district + 1), 1)
    district = _trim_middle(district, district_len_limit)
    return "|".join([*prefix_parts, address, district, *suffix_parts])


def format_object_list_line(index: int, obj: Property) -> str:
    return f"{index}. {format_object_compact(obj, with_status=False)}"


def format_object_list_item(index: int, prop: Property) -> str:
    return f"{index}. {format_object_compact(prop)}"


def format_properties_list(properties: list[Property], title: str, limit: int) -> str:
    rows = [f"{title}", ""]

    for index, prop in enumerate(properties, start=1):
        rows.append(format_object_list_line(index=index, obj=prop))

    rows.extend(["", f"Показаны первые {min(len(properties), limit)} записей."])
    return "\n".join(rows)


def format_property_card(property_obj: Property, manager_name: str, updated: bool = False) -> str:
    header = f"Карточка объекта #{safe_html(property_obj.id)}"
    if updated:
        header = f"✅ Карточка объекта обновлена\n\n{header}"

    property_type = safe_html(PROPERTY_TYPE_LABELS.get(property_obj.property_type, property_obj.property_type.value))
    status = safe_html(format_property_status(property_obj))
    floor_row = f"Этаж: {safe_html(property_obj.floor)}\n"
    if property_obj.property_type == PropertyType.APARTMENT:
        floor_row = (
            f"Этаж: {safe_html(property_obj.floor)} "
            f"из {safe_html(property_obj.building_floors)}\n"
        )

    return (
        f"{header}\n\n"
        f"ID объекта: {safe_html(property_obj.id)}\n"
        f"Название: {safe_html(property_obj.title)}\n"
        f"Тип недвижимости: {property_type}\n"
        f"Район: {safe_html(property_obj.district)}\n"
        f"<b>Адрес:</b> {safe_html(format_property_address_for_display(property_obj.district, property_obj.address))}\n"
        f"<b>Номер владельца:</b> {format_owner_phone(property_obj.owner_phone)}\n"
        f"<b>Цена:</b> {safe_html(_format_money(property_obj.price))}\n"
        f"<b>Площадь:</b> {safe_html(format_area(property_obj.area))}\n"
        f"<b>Кухня:</b> {safe_html(format_area(property_obj.kitchen_area))}\n"
        f"<b>Комнаты:</b> {safe_html(property_obj.rooms)}\n"
        f"{floor_row}"
        f"<b>Год постройки:</b> {safe_html(property_obj.building_year)}\n"
        f"<b>Материал дома:</b> {safe_html(property_obj.building_material)}\n"
        f"<b>Описание:</b> {safe_html(property_obj.description)}\n"
        f"<b>Ссылка:</b> {safe_html(property_obj.link)}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Ответственный менеджер:</b> {safe_html(manager_name)}\n"
        f"<b>Дата создания:</b> {safe_html(_format_datetime(property_obj.created_at))}\n"
        f"<b>Дата обновления:</b> {safe_html(_format_datetime(property_obj.updated_at))}"
    )


def _format_share_value(value: object) -> str:
    if value is None:
        return "—"
    text = str(value).strip()
    return text or "—"


def _format_house_number_for_share(property_obj: Property) -> str:
    address = format_property_address_for_display(property_obj.district, property_obj.address)
    if not address or address in {"-", "—"}:
        return "—"

    match = _HOUSE_NUMBER_RE.search(address)
    if match:
        return match.group(1)

    stripped = address.strip()
    if re.fullmatch(r"\d+[\w/-]*", stripped):
        return stripped
    return stripped


def _format_area_for_share(property_obj: Property) -> str:
    area = _format_decimal(property_obj.area)
    kitchen = _format_decimal(property_obj.kitchen_area)
    if area == "—" and kitchen == "—":
        return "—"
    if kitchen == "—":
        return area
    return f"{area}/{kitchen}"


def _format_location_for_share(property_obj: Property) -> str:
    district = (property_obj.district or "").strip()
    if district:
        return f"Мкр {district}"

    title = (property_obj.title or "").strip()
    if title:
        return title

    address = format_property_address_for_display(property_obj.district, property_obj.address)
    return address if address and address != "-" else "—"


def _format_public_location_for_share(property_obj: Property) -> str:
    district = (property_obj.district or "").strip()
    return f"Мкр {district}" if district else "Мкр —"


def format_property_info_text(property_obj: Property, manager_name: str) -> str:
    return "\n".join(
        [
            _format_location_for_share(property_obj),
            f"Дом: {_format_house_number_for_share(property_obj)}",
            f"Комнат: {_format_share_value(property_obj.rooms)}",
            f"Этаж: {format_floor_short(property_obj.floor, property_obj.building_floors)}",
            f"Площадь: {_format_area_for_share(property_obj)}",
            f"Материал стен: {_format_share_value(property_obj.building_material).lower()}",
            f"Год: {_format_share_value(property_obj.building_year)}",
            f"Цена: {_format_money_for_share(property_obj.price)}",
            f"Осмотрел: {_format_share_value(manager_name)}",
        ]
    )


def format_property_public_info_text(property_obj: Property) -> str:
    return "\n".join(
        [
            _format_public_location_for_share(property_obj),
            f"Комнат: {_format_share_value(property_obj.rooms)}",
            f"Этаж: {format_floor_short(property_obj.floor, property_obj.building_floors)}",
            f"Площадь: {_format_area_for_share(property_obj)}",
            f"Материал стен: {_format_share_value(property_obj.building_material).lower()}",
            f"Год: {_format_share_value(property_obj.building_year)}",
        ]
    )


def format_property_info_message(property_obj: Property, manager_name: str) -> str:
    info_text = escape(format_property_info_text(property_obj=property_obj, manager_name=manager_name), quote=False)
    return f"Информация для отправки:\n\n<pre>{info_text}</pre>"


def format_property_public_info_message(property_obj: Property) -> str:
    info_text = escape(format_property_public_info_text(property_obj=property_obj), quote=False)
    return f"Информация для клиента:\n\n<pre>{info_text}</pre>"


def format_property_status(property_obj: Property) -> str:
    if property_obj.status == PropertyStatus.REFUSED_TO_WORK:
        refused_names = (getattr(property_obj, "refused_manager_names", None) or "").strip()
        if refused_names:
            return f"Отказ. работать с {refused_names}"
    return PROPERTY_STATUS_LABELS.get(property_obj.status, property_obj.status.value)


def format_property_created_card(property_obj: Property, manager_name: str) -> str:
    return "✅ <b>Объект успешно создан</b>\n\n" + format_property_card(property_obj=property_obj,
                                                                       manager_name=manager_name)


def format_duplicate_property_card(property_obj: Property, matched_fields: list[str], matched_count: int) -> str:
    labels = {
        "owner_phone_normalized": "телефон",
        "floor": "этаж",
        "building_floors": "этажность",
        "building_year": "год",
        "price": "цена",
        "rooms": "комнаты",
        "area": "площадь",
    }
    matched_lines = "\n".join(f"- {labels.get(field, field)}" for field in matched_fields) or "- —"
    return (
        f"⚠️ Похоже, такой объект уже есть в базе.\n\n"
        f"ID: {safe_html(property_obj.id)}\n"
        f"Район: {safe_html(property_obj.district)}\n"
        f"Адрес: {safe_html(format_property_address_for_display(property_obj.district, property_obj.address))}\n"
        f"Телефон: {format_owner_phone(property_obj.owner_phone)}\n"
        f"Цена: {safe_html(_format_money(property_obj.price))}\n"
        f"Комнаты: {safe_html(property_obj.rooms)}\n"
        f"Площадь: {safe_html(format_area(property_obj.area))}\n"
        f"Этаж/Этажность: {safe_html(property_obj.floor)}/{safe_html(property_obj.building_floors)}\n"
        f"Год: {safe_html(property_obj.building_year)}\n\n"
        f"Совпадение: {safe_html(matched_count)} из 7\n"
        f"Совпали:\n{matched_lines}\n\n"
        f"Вы точно хотите добавить новый объект?"
    )
