from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.common.enums import PropertyStatus, PropertyType
from app.database.models.property import Property

PROPERTY_TYPE_LABELS: dict[PropertyType, str] = {
    PropertyType.APARTMENT: "Квартира",
    PropertyType.HOUSE: "Дом",
    PropertyType.COMMERCIAL: "Коммерческая",
    PropertyType.LAND: "Участок",
}

PROPERTY_STATUS_LABELS: dict[PropertyStatus, str] = {
    PropertyStatus.ACTIVE: "Активен",
    PropertyStatus.RESERVED: "Сдан",
    PropertyStatus.SOLD: "Продан",
    PropertyStatus.ARCHIVED: "Архив",
}


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


def format_properties_list(properties: list[Property], title: str, limit: int) -> str:
    rows = [f"<b>{title}</b>", ""]

    for index, prop in enumerate(properties, start=1):
        status = PROPERTY_STATUS_LABELS.get(prop.status, prop.status.value)
        price = _format_money(prop.price)
        rows.append(f"{index}. <b>{prop.title}</b> · {prop.district} · {price} · {status}")

    rows.extend(["", f"Показаны первые {min(len(properties), limit)} записей."])
    return "\n".join(rows)


def format_property_card(property_obj: Property, manager_name: str, updated: bool = False) -> str:
    header = f"<b>Карточка объекта #{property_obj.id}</b>"
    if updated:
        header = f"✅ <b>Карточка объекта обновлена</b>\n\n{header}"

    property_type = PROPERTY_TYPE_LABELS.get(property_obj.property_type, property_obj.property_type.value)
    status = PROPERTY_STATUS_LABELS.get(property_obj.status, property_obj.status.value)

    return (
        f"{header}\n\n"
        f"<b>ID объекта:</b> {property_obj.id}\n"
        f"<b>Название:</b> {property_obj.title}\n"
        f"<b>Тип недвижимости:</b> {property_type}\n"
        f"<b>Район:</b> {property_obj.district or '—'}\n"
        f"<b>Адрес:</b> {property_obj.address or '—'}\n"
        f"<b>Цена:</b> {_format_money(property_obj.price)}\n"
        f"<b>Площадь (м²):</b> {_format_decimal(property_obj.area)}\n"
        f"<b>Комнаты:</b> {property_obj.rooms if property_obj.rooms is not None else '—'}\n"
        f"<b>Этаж:</b> {property_obj.floor if property_obj.floor is not None else '—'}\n"
        f"<b>Описание:</b> {property_obj.description or '—'}\n"
        f"<b>Ссылка:</b> {property_obj.link or '—'}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Ответственный менеджер:</b> {manager_name}\n"
        f"<b>Дата создания:</b> {_format_datetime(property_obj.created_at)}\n"
        f"<b>Дата обновления:</b> {_format_datetime(property_obj.updated_at)}"
    )


def format_property_created_card(property_obj: Property, manager_name: str) -> str:
    return "✅ <b>Объект успешно создан</b>\n\n" + format_property_card(property_obj=property_obj, manager_name=manager_name)