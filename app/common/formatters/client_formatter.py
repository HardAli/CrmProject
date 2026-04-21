from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.common.enums import ClientStatus, PropertyType, RequestType
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


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    local_dt = value.astimezone(timezone.utc)
    return local_dt.strftime("%d.%m.%Y %H:%M UTC")


def _format_budget_range(client: Client) -> str:
    return f"{_format_money(client.budget_min)} - {_format_money(client.budget_max)}"


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


def format_client_card(client: Client, manager_name: str, updated: bool = False) -> str:
    status = STATUS_LABELS.get(client.status, client.status.value)
    request_type = REQUEST_TYPE_LABELS.get(client.request_type, client.request_type.value)
    property_type = PROPERTY_TYPE_LABELS.get(client.property_type, client.property_type.value)

    header = f"<b>Карточка клиента #{client.id}</b>"
    if updated:
        header = f"✅ <b>Карточка обновлена</b>\n\n{header}"

    return (
        f"{header}\n\n"
        f"<b>ID клиента:</b> {client.id}\n"
        f"<b>Имя:</b> {client.full_name}\n"
        f"<b>Телефон:</b> {format_phone_for_copy(client.phone)}\n"
        f"<b>Источник:</b> {client.source or '—'}\n"
        f"<b>Тип запроса:</b> {request_type}\n"
        f"<b>Тип недвижимости:</b> {property_type}\n"
        f"<b>Район:</b> {client.district or '—'}\n"
        f"<b>Комнаты:</b> {client.rooms if client.rooms is not None else '—'}\n"
        f"<b>Бюджет:</b> {_format_budget_range(client)}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Последняя заметка:</b> {client.note or '—'}\n"
        f"<b>Следующий контакт:</b> {_format_datetime(client.next_contact_at)}\n"
        f"<b>Ответственный менеджер:</b> {manager_name}\n"
        f"<b>Дата создания:</b> {_format_datetime(client.created_at)}\n"
        f"<b>Дата обновления:</b> {_format_datetime(client.updated_at)}"
    )