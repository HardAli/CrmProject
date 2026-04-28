from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from html import escape

from app.common.enums import PropertyStatus, PropertyType
from app.common.utils.phone_links import format_owner_phone
from app.database.models.property import Property

PROPERTY_TYPE_LABELS: dict[PropertyType, str] = {
    PropertyType.APARTMENT: "Квартира",
    PropertyType.HOUSE: "Дом",
    PropertyType.COMMERCIAL: "Коммерческая",
    PropertyType.LAND: "Участок",
}

PROPERTY_STATUS_LABELS: dict[PropertyStatus, str] = {
    PropertyStatus.ACTIVE: "Активен",
    PropertyStatus.RESERVED: "Забронирован",
    PropertyStatus.SOLD: "Продан",
    PropertyStatus.ARCHIVED: "Архив",
}


def safe_html(value: object) -> str:
    if value is None:
        return "—"
    return escape(str(value), quote=False)


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "—"
    normalized = value.normalize()
    return f"{normalized}"


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


def format_area_short(area: Decimal | None) -> str:
    if area is None:
        return "—"
    normalized = area.normalize()
    return f"{normalized}м²"


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
    normalized = mln_value.normalize()
    return f"{normalized} млн"


def _trim_middle(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    if max_len <= 1:
        return value[:max_len]
    return f"{value[: max_len - 1]}…"


def format_object_compact(prop: Property, with_status: bool = True, max_length: int | None = None) -> str:
    status = PROPERTY_STATUS_LABELS.get(prop.status, prop.status.value)
    prefix_parts = [
        format_rooms_short(prop.rooms, prop.title),
        format_area_short(prop.area),
        format_floor_short(prop.floor, prop.building_floors),
    ]
    address = prop.address or prop.title or "—"
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
    rows = [f"<b>{title}</b>", ""]

    for index, prop in enumerate(properties, start=1):
        rows.append(format_object_list_line(index=index, obj=prop))

    rows.extend(["", f"Показаны первые {min(len(properties), limit)} записей."])
    return "\n".join(rows)


def format_property_card(property_obj: Property, manager_name: str, updated: bool = False) -> str:
    header = f"<b>Карточка объекта #{safe_html(property_obj.id)}</b>"
    if updated:
        header = f"✅ <b>Карточка объекта обновлена</b>\n\n{header}"

    property_type = safe_html(PROPERTY_TYPE_LABELS.get(property_obj.property_type, property_obj.property_type.value))
    status = safe_html(PROPERTY_STATUS_LABELS.get(property_obj.status, property_obj.status.value))
    floor_row = f"<b>Этаж:</b> {safe_html(property_obj.floor)}\n"
    if property_obj.property_type == PropertyType.APARTMENT:
        floor_row = (
            f"<b>Этаж:</b> {safe_html(property_obj.floor)} "
            f"из {safe_html(property_obj.building_floors)}\n"
        )

    return (
        f"{header}\n\n"
        f"<b>ID объекта:</b> {safe_html(property_obj.id)}\n"
        f"<b>Название:</b> {safe_html(property_obj.title)}\n"
        f"<b>Тип недвижимости:</b> {property_type}\n"
        f"<b>Район:</b> {safe_html(property_obj.district)}\n"
        f"<b>Адрес:</b> {safe_html(property_obj.address)}\n"
        f"<b>Номер владельца:</b> {format_owner_phone(property_obj.owner_phone)}\n"
        f"<b>Цена:</b> {safe_html(_format_money(property_obj.price))}\n"
        f"<b>Площадь (м²):</b> {safe_html(_format_decimal(property_obj.area))}\n"
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


def format_property_created_card(property_obj: Property, manager_name: str) -> str:
    return "✅ <b>Объект успешно создан</b>\n\n" + format_property_card(property_obj=property_obj,
                                                                       manager_name=manager_name)
