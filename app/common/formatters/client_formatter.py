from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.common.enums import ClientStatus, PropertyType, RequestType, WallMaterial
from app.common.utils.phone_links import format_phone_for_copy
from app.database.models.client import Client

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


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    local_dt = value.astimezone(timezone.utc)
    return local_dt.strftime("%d.%m.%Y %H:%M UTC")


def format_client_created_card(client: Client, manager_name: str) -> str:
    return "✅ <b>Клиент успешно создан</b>\n\n" + format_client_card(client=client, manager_name=manager_name)


def format_clients_list(clients: list[Client], title: str, limit: int) -> str:
    rows = [f"<b>{title}</b>", ""]
    for index, client in enumerate(clients, start=1):
        status = STATUS_LABELS.get(client.status, client.status.value)
        rows.append(
            f"{index}. <b>{client.full_name}</b> · {status}\n"
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


def format_client_compact(client: Client) -> str:
    name = (client.full_name or "").strip() or client.phone
    deal_type = REQUEST_TYPE_LABELS.get(client.request_type, client.request_type.value)
    need = client.rooms or "—"
    budget = _format_budget_short(client.budget)
    district = client.district or "—"
    status = STATUS_LABELS.get(client.status, client.status.value)
    return f"{name}|{deal_type}|{need}|{budget}|{district}|{status}"


def format_client_list_line(index: int, client: Client) -> str:
    return f"{index}. {format_client_compact(client)}"


def build_client_filters_summary(filters: dict[str, Any]) -> str:
    quick_filter = filters.get("quick_filter")
    if quick_filter:
        return quick_filter

    chunks: list[str] = []
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
    rows = [
        "<b>Мои клиенты</b>",
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
        f"Статус: {status_label}\n"
        f"Сделка: {deal}\n"
        f"Комн.: {rooms}\n"
        f"Бюджет: {budget}\n"
        f"Район: {district}\n"
        f"Контакт: {contact}"
    )


def format_client_card(client: Client, manager_name: str, updated: bool = False) -> str:
    status = STATUS_LABELS.get(client.status, client.status.value)
    request_type = REQUEST_TYPE_LABELS.get(client.request_type, client.request_type.value)
    property_type = PROPERTY_TYPE_LABELS.get(client.property_type, client.property_type.value)

    header = f"<b>Карточка клиента #{client.id}</b>"
    if updated:
        header = f"✅ <b>Карточка обновлена</b>\n\n{header}"

    apartment_rows = ""
    if client.floor is not None:
        apartment_rows += f"<b>Этаж:</b> {client.floor}\n"
    if client.building_floors is not None:
        apartment_rows += f"<b>Этажность дома:</b> {client.building_floors}\n"
    if client.wall_material is not None:
        wall_material = WALL_MATERIAL_LABELS.get(client.wall_material, client.wall_material.value)
        apartment_rows += f"<b>Материал стен:</b> {wall_material}\n"
    if client.year_built is not None:
        apartment_rows += f"<b>Год постройки:</b> {client.year_built}\n"

    return (
        f"{header}\n\n"
        f"<b>ID клиента:</b> {client.id}\n"
        f"<b>Имя:</b> {client.full_name}\n"
        f"<b>Телефон:</b> {format_phone_for_copy(client.phone)}\n"
        f"<b>Источник:</b> {client.source or '—'}\n"
        f"<b>Тип запроса:</b> {request_type}\n"
        f"<b>Тип недвижимости:</b> {property_type}\n"
        f"<b>Район:</b> {client.district or '—'}\n"
        f"<b>Комнаты:</b> {client.rooms or '—'}\n"
        f"<b>Цена:</b> {_format_money(client.budget)}\n"
        f"{apartment_rows}"
        f"<b>Статус:</b> {status}\n"
        f"<b>Последняя заметка:</b> {client.note or '—'}\n"
        f"<b>Следующий контакт:</b> {_format_datetime(client.next_contact_at)}\n"
        f"<b>Ответственный менеджер:</b> {manager_name}\n"
        f"<b>Дата создания:</b> {_format_datetime(client.created_at)}\n"
        f"<b>Дата обновления:</b> {_format_datetime(client.updated_at)}"
    )
