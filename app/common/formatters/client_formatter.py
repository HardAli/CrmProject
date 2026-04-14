from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.database.models.client import Client


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    local_dt = value.astimezone(timezone.utc)
    return local_dt.strftime("%d.%m.%Y %H:%M UTC")


def format_client_card(client: Client, manager_name: str) -> str:
    return (
        "✅ <b>Клиент успешно создан</b>\n\n"
        f"<b>ID клиента:</b> {client.id}\n"
        f"<b>Имя:</b> {client.full_name}\n"
        f"<b>Телефон:</b> {client.phone}\n"
        f"<b>Источник:</b> {client.source or '—'}\n"
        f"<b>Тип запроса:</b> {client.request_type.value}\n"
        f"<b>Тип недвижимости:</b> {client.property_type.value}\n"
        f"<b>Район:</b> {client.district or '—'}\n"
        f"<b>Комнаты:</b> {client.rooms if client.rooms is not None else '—'}\n"
        f"<b>Бюджет:</b> {_format_money(client.budget_min)} - {_format_money(client.budget_max)}\n"
        f"<b>Заметка:</b> {client.note or '—'}\n"
        f"<b>Следующий контакт:</b> {_format_datetime(client.next_contact_at)}\n"
        f"<b>Ответственный менеджер:</b> {manager_name}\n"
        f"<b>Дата создания:</b> {_format_datetime(client.created_at)}"
    )