from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import escape
from typing import Any

from app.common.enums import ClientStatus, PropertyType, RequestType, WallMaterial
from app.common.formatters.property_formatter import (
    EMPTY_SHORT,
    format_button_compact_text,
    format_material_short,
    format_price_short,
    format_property_floor_short,
    format_property_info_text,
    format_property_public_info_text,
    format_property_type_short,
    format_rooms_list_short,
    format_seller_list_button,
    format_year_short,
)
from app.common.utils.phone_links import format_phone_for_copy, format_phone_for_display
from app.database.models.client import Client
from app.database.models.property import Property

STATUS_LABELS: dict[ClientStatus, str] = {
    ClientStatus.NEW: "Новый",
    ClientStatus.IN_PROGRESS: "В работе",
    ClientStatus.WAITING: "Ждёт звонка",
    ClientStatus.SHOWING: "Показ",
    ClientStatus.CLOSED_SUCCESS: "Закрыт",
    ClientStatus.CLOSED_FAILED: "Отказ",
}

REQUEST_TYPE_LABELS: dict[RequestType, str] = {
    RequestType.BUY: "Купить",
    RequestType.SELL: "Продать",
    RequestType.RENT: "Снять",
    RequestType.RENT_OUT: "Сдать",
}

PROPERTY_TYPE_LABELS: dict[PropertyType, str] = {
    PropertyType.APARTMENT: "Квартира",
    PropertyType.HOUSE: "Дом",
    PropertyType.COMMERCIAL: "Коммерческая",
    PropertyType.LAND: "Участок",
}

WALL_MATERIAL_LABELS: dict[WallMaterial, str] = {
    WallMaterial.BRICK: "Кирпич",
    WallMaterial.PANEL: "Панель",
    WallMaterial.MONOLITH: "Монолит",
}


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def _format_money_for_share(value: Decimal | None) -> str:
    return _format_money(value).replace(" ", ".")


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    local_dt = value.astimezone(timezone.utc)
    return local_dt.strftime("%d.%m.%Y %H:%M UTC")


def _html(value: object) -> str:
    if value is None:
        return "—"
    return escape(str(value), quote=False)


def _format_share_value(value: object) -> str:
    if value is None:
        return "—"
    text = str(value).strip()
    return text or "—"


def format_client_created_card(client: Client, manager_name: str) -> str:
    return "✅ Клиент успешно создан\n\n" + format_client_card(client=client, manager_name=manager_name)


def format_clients_list(clients: list[Client], title: str, limit: int) -> str:
    rows = [f"{title}", ""]
    for index, client in enumerate(clients, start=1):
        status = STATUS_LABELS.get(client.status, client.status.value)
        rows.append(
            f"{index}. {_html(client.full_name)} · {_html(status)}\n"
            f"   Телефон: {format_phone_for_copy(client.phone)}"
        )

    rows.extend(["", f"Показаны первые {min(len(clients), limit)} записей."])
    return "\n".join(rows)


def _format_budget_short(value: Decimal | None) -> str:
    if value is None:
        return "—"
    numeric = int(value)
    if numeric >= 1_000_000:
        return f"до {numeric // 1_000_000}"
    if numeric >= 1_000:
        return f"до {numeric // 1_000}к"
    return f"до {numeric}"


def format_client_budget_compact(value: object) -> str:
    """
    19500000 -> "19.5"
    19000000 -> "19"
    25000000 -> "25"
    None -> "—"
    """
    if value is None:
        return "—"

    try:
        amount = Decimal(str(value).replace(" ", ""))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)

    if amount >= Decimal("1000000"):
        amount = amount / Decimal("1000000")
    elif amount >= Decimal("1000"):
        thousands = amount / Decimal("1000")
        thousands_text = format(thousands.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f")
        if thousands_text.endswith(".0"):
            thousands_text = thousands_text[:-2]
        return f"{thousands_text}к"

    text = format(amount.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f")
    if text.endswith(".0"):
        text = text[:-2]
    return text


def format_client_compact(client: Client) -> str:
    name = (client.full_name or "").strip() or client.phone
    deal_type = REQUEST_TYPE_LABELS.get(client.request_type, client.request_type.value)
    need = client.rooms or "—"
    budget = format_client_budget_compact(client.budget)
    district = client.district or "—"
    status = STATUS_LABELS.get(client.status, client.status.value)
    return f"{name}|{deal_type}|{need}|{budget}|{district}|{status}"


def format_client_list_line(index: int, client: Client) -> str:
    return f"{index}. {format_client_compact(client)}"


def _is_seller_filters(filters: dict[str, Any]) -> bool:
    deal_types = set(filters.get("deal_types") or [])
    return RequestType.SELL.value in deal_types and len(deal_types) == 1


def _get_loaded_seller_property(client: Client) -> Property | None:
    links = client.__dict__.get("properties")
    if not links:
        return None
    for link in links:
        property_obj = getattr(link, "property", None)
        if property_obj is not None:
            return property_obj
    return None


def format_seller_client_button(client: Client, max_length: int | None = None) -> str:
    property_obj = _get_loaded_seller_property(client)
    if property_obj is not None:
        return format_seller_list_button(property_obj, max_length=max_length)

    parts = [
        format_price_short(client.budget),
        format_rooms_list_short(client.rooms),
        format_property_floor_short(client.floor, client.building_floors),
        client.district or EMPTY_SHORT,
        EMPTY_SHORT,
        format_material_short(client.wall_material),
        format_year_short(year=client.year_built),
        format_property_type_short(client.property_type),
    ]
    return format_button_compact_text("|".join(parts), max_length)


def build_client_filters_summary(filters: dict[str, Any]) -> str:
    quick_filter = filters.get("quick_filter")
    if quick_filter:
        return quick_filter

    chunks: list[str] = []
    deal_types = filters.get("deal_types") or []
    if deal_types:
        deal_labels = []
        for deal_type in deal_types:
            try:
                deal_labels.append(REQUEST_TYPE_LABELS[RequestType(deal_type)])
            except ValueError:
                deal_labels.append(str(deal_type))
        chunks.append(",".join(deal_labels))
    if filters.get("rooms"):
        chunks.append(",".join(filters["rooms"]))
    if filters.get("budget_max"):
        max_budget = int(filters["budget_max"])
        chunks.append(f"до {max_budget // 1_000_000}" if max_budget >= 1_000_000 else f"до {max_budget}")
    if filters.get("districts"):
        chunks.append(",".join(filters["districts"][:2]))
    if filters.get("next_contact_mode"):
        chunks.append(str(filters["next_contact_mode"]))
    if filters.get("task_mode"):
        chunks.append(str(filters["task_mode"]))
    if filters.get("search_query"):
        chunks.append(str(filters["search_query"]))

    if chunks:
        return "|".join(chunks)
    return "активные"


def build_clients_list_text(
    clients: list[Client],
    filters: dict[str, Any],
    total_count: int,
    page: int,
    per_page: int,
) -> str:
    if _is_seller_filters(filters):
        rows = [
            "База продавцов",
            "",
            "Номер | Комнаты | Цена | Район | Квадратура | Этаж/Этажность | Год | Материал | Тип",
            "",
            f"Найдено: {total_count} | Страница: {page}",
            "",
        ]
        if not clients:
            rows.append("Продавцы не найдены.")
        else:
            start_index = (page - 1) * per_page + 1
            for index, client in enumerate(clients, start=start_index):
                rows.append(f"{index} | {format_seller_client_button(client)}")
        return "\n".join(rows)

    rows = [
        "Клиенты",
        "",
        f"Фильтр: {build_client_filters_summary(filters)}",
        f"Найдено: {total_count}",
        "",
    ]
    start_index = (page - 1) * per_page + 1
    for idx, client in enumerate(clients, start=start_index):
        rows.append(format_client_list_line(idx, client))
    if not clients:
        rows.append("Клиенты не найдены.")
    return "\n".join(rows)


def build_client_filters_menu_text(filters: dict[str, Any]) -> str:
    statuses = filters.get("statuses") or []
    status_label = "активные" if len(statuses) == 4 else ("все" if len(statuses) == len(ClientStatus) else "выбрано")
    deal = "любая" if not filters.get("deal_types") else "выбрано"
    rooms = "любые" if not filters.get("rooms") else ",".join(filters["rooms"])
    budget = "любой"
    if filters.get("budget_min") or filters.get("budget_max"):
        budget = f"{filters.get('budget_min') or 0}-{filters.get('budget_max') or '∞'}"
    district = "любой" if not filters.get("districts") else ",".join(filters["districts"][:2])
    contact = "любой" if not filters.get("next_contact_mode") else str(filters["next_contact_mode"])
    return (
        "<b>Фильтры клиентов</b>\n\n"
        f"Статус: {_html(status_label)}\n"
        f"Сделка: {_html(deal)}\n"
        f"Комн.: {_html(rooms)}\n"
        f"Бюджет: {_html(budget)}\n"
        f"Район: {_html(district)}\n"
        f"Контакт: {_html(contact)}"
    )


def format_client_card(client: Client, manager_name: str, updated: bool = False) -> str:
    status = STATUS_LABELS.get(client.status, client.status.value)
    request_type = REQUEST_TYPE_LABELS.get(client.request_type, client.request_type.value)
    property_type = PROPERTY_TYPE_LABELS.get(client.property_type, client.property_type.value)

    header = f"<b>Карточка клиента #{_html(client.id)}</b>"
    if updated:
        header = f"✅ <b>Карточка обновлена</b>\n\n{header}"

    apartment_rows = ""
    if client.floor is not None:
        apartment_rows += f"<b>Этаж:</b> {_html(client.floor)}\n"
    if client.building_floors is not None:
        apartment_rows += f"<b>Этажность дома:</b> {_html(client.building_floors)}\n"
    if client.wall_material is not None:
        wall_material = WALL_MATERIAL_LABELS.get(client.wall_material, client.wall_material.value)
        apartment_rows += f"<b>Материал стен:</b> {_html(wall_material)}\n"
    if client.year_built is not None:
        apartment_rows += f"<b>Год постройки:</b> {_html(client.year_built)}\n"

    return (
        f"{header}\n\n"
        f"<b>ID клиента:</b> {_html(client.id)}\n"
        f"<b>Имя:</b> {_html(client.full_name)}\n"
        f"<b>Телефон:</b> {format_phone_for_copy(client.phone)}\n"
        f"<b>Источник:</b> {_html(client.source)}\n"
        f"<b>Тип запроса:</b> {_html(request_type)}\n"
        f"<b>Тип недвижимости:</b> {_html(property_type)}\n"
        f"<b>Район:</b> {_html(client.district)}\n"
        f"<b>Комнаты:</b> {_html(client.rooms)}\n"
        f"<b>Цена:</b> {_html(_format_money(client.budget))}\n"
        f"{apartment_rows}"
        f"<b>Статус:</b> {_html(status)}\n"
        f"<b>Последняя заметка:</b> {_html(client.note)}\n"
        f"<b>Следующий контакт:</b> {_html(_format_datetime(client.next_contact_at))}\n"
        f"<b>Ответственный менеджер:</b> {_html(manager_name)}\n"
        f"<b>Дата создания:</b> {_html(_format_datetime(client.created_at))}\n"
        f"<b>Дата обновления:</b> {_html(_format_datetime(client.updated_at))}"
    )


def _format_seller_client_info_text(client: Client, manager_name: str) -> str:
    property_obj = _get_loaded_seller_property(client)
    if property_obj is not None:
        return format_property_info_text(property_obj=property_obj, manager_name=manager_name)

    wall_material = client.wall_material
    if wall_material is not None:
        wall_material_text = WALL_MATERIAL_LABELS.get(wall_material, wall_material.value).lower()
    else:
        wall_material_text = "—"

    district = _format_share_value(client.district)
    district_line = f"Мкр {district}" if district != "—" else "Мкр —"
    return "\n".join(
        [
            district_line,
            "Дом: —",
            f"Комнат: {_format_share_value(client.rooms)}",
            f"Этаж: {format_property_floor_short(client.floor, client.building_floors)}",
            "Площадь: —",
            f"Материал стен: {wall_material_text}",
            f"Год: {_format_share_value(client.year_built)}",
            f"Цена: {_format_money_for_share(client.budget)}",
            f"Осмотрел: {_format_share_value(manager_name)}",
        ]
    )


def _format_seller_client_public_info_text(client: Client) -> str:
    property_obj = _get_loaded_seller_property(client)
    if property_obj is not None:
        return format_property_public_info_text(property_obj=property_obj)

    wall_material = client.wall_material
    if wall_material is not None:
        wall_material_text = WALL_MATERIAL_LABELS.get(wall_material, wall_material.value).lower()
    else:
        wall_material_text = "—"

    district = _format_share_value(client.district)
    district_line = f"Мкр {district}" if district != "—" else "Мкр —"
    return "\n".join(
        [
            district_line,
            f"Комнат: {_format_share_value(client.rooms)}",
            f"Этаж: {format_property_floor_short(client.floor, client.building_floors)}",
            "Площадь: —",
            f"Материал стен: {wall_material_text}",
            f"Год: {_format_share_value(client.year_built)}",
        ]
    )


def format_client_info_text(client: Client, manager_name: str) -> str:
    if client.request_type == RequestType.SELL:
        return _format_seller_client_info_text(client=client, manager_name=manager_name)

    request_type = REQUEST_TYPE_LABELS.get(client.request_type, client.request_type.value)
    return "\n".join(
        [
            f"Клиент: {_format_share_value(client.full_name)}",
            f"Телефон: {format_phone_for_display(client.phone)}",
            f"Запрос: {_format_share_value(request_type)}",
            f"Район: {_format_share_value(client.district)}",
            f"Комнат: {_format_share_value(client.rooms)}",
            f"Бюджет: {_format_money_for_share(client.budget)}",
            f"Ответственный: {_format_share_value(manager_name)}",
        ]
    )


def format_client_public_info_text(client: Client) -> str:
    if client.request_type == RequestType.SELL:
        return _format_seller_client_public_info_text(client=client)

    request_type = REQUEST_TYPE_LABELS.get(client.request_type, client.request_type.value)
    return "\n".join(
        [
            f"Клиент: {_format_share_value(client.full_name)}",
            f"Телефон: {format_phone_for_display(client.phone)}",
            f"Запрос: {_format_share_value(request_type)}",
            f"Район: {_format_share_value(client.district)}",
            f"Комнат: {_format_share_value(client.rooms)}",
        ]
    )


def format_client_info_message(client: Client, manager_name: str) -> str:
    info_text = escape(format_client_info_text(client=client, manager_name=manager_name), quote=False)
    return f"Информация для отправки:\n\n<pre>{info_text}</pre>"


def format_client_public_info_message(client: Client) -> str:
    info_text = escape(format_client_public_info_text(client=client), quote=False)
    return f"Информация для клиента:\n\n<pre>{info_text}</pre>"
