from __future__ import annotations

from decimal import Decimal
from html import escape

from app.common.formatters.client_formatter import REQUEST_TYPE_LABELS, STATUS_LABELS
from app.common.formatters.property_address_formatter import format_property_address_for_display
from app.common.formatters.property_formatter import PROPERTY_STATUS_LABELS
from app.common.utils.phone_links import format_phone_for_copy
from app.database.models.client import Client
from app.database.models.property import Property


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def format_client_search_results(clients: list[Client], limit: int) -> str:
    rows = ["<b>Результаты поиска клиентов</b>", ""]
    for index, client in enumerate(clients, start=1):
        status = STATUS_LABELS.get(client.status, client.status.value)
        rows.append(
            f"{index}. <b>{client.full_name}</b> · {client.district or '—'} · {status}\n"
            f"   Телефон: {format_phone_for_copy(client.phone)}"
        )

    rows.extend(["", f"Найдено: {len(clients)} (лимит: {limit})."])
    return "\n".join(rows)


def format_property_search_results(properties: list[Property], limit: int) -> str:
    rows = ["<b>Результаты поиска объектов</b>", ""]
    for index, property_obj in enumerate(properties, start=1):
        status = PROPERTY_STATUS_LABELS.get(property_obj.status, property_obj.status.value)
        address = format_property_address_for_display(property_obj.district, property_obj.address)
        rows.append(
            f"{index}. <b>{escape(property_obj.title)}</b> · {escape(property_obj.district or '—')} · "
            f"{escape(address)} · {escape(_format_money(property_obj.price))} · {escape(status)}"
        )

    rows.extend(["", f"Найдено: {len(properties)} (лимит: {limit})."])
    return "\n".join(rows)


def format_client_search_applied_filters(filters: dict[str, object]) -> str:
    rows: list[str] = []
    if filters.get("full_name"):
        rows.append(f"• Имя: {filters['full_name']}")
    if filters.get("phone"):
        rows.append(f"• Телефон: {filters['phone']}")
    if filters.get("district"):
        rows.append(f"• Район: {filters['district']}")
    if filters.get("status"):
        rows.append(f"• Статус: {STATUS_LABELS.get(filters['status'], str(filters['status']))}")
    if filters.get("request_type"):
        rows.append(f"• Тип запроса: {REQUEST_TYPE_LABELS.get(filters['request_type'], str(filters['request_type']))}")

    return "\n".join(rows)


def format_property_search_applied_filters(filters: dict[str, object]) -> str:
    rows: list[str] = []
    if filters.get("search_text"):
        rows.append(f"• Запрос: {escape(str(filters['search_text']))}")
    if filters.get("title"):
        rows.append(f"• Название: {escape(str(filters['title']))}")
    if filters.get("district"):
        rows.append(f"• Район: {escape(str(filters['district']))}")
    if filters.get("property_type"):
        rows.append(f"• Тип: {escape(str(filters['property_type']))}")
    if filters.get("status"):
        status = PROPERTY_STATUS_LABELS.get(filters["status"], str(filters["status"]))
        rows.append(f"• Статус: {escape(status)}")
    if filters.get("price_min") is not None:
        rows.append(f"• Цена от: {_format_money(filters['price_min'])}")
    if filters.get("price_max") is not None:
        rows.append(f"• Цена до: {_format_money(filters['price_max'])}")
    if filters.get("rooms") is not None:
        rows.append(f"• Комнаты: {filters['rooms']}")

    return "\n".join(rows)
