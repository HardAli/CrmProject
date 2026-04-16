from __future__ import annotations

from decimal import Decimal

from app.common.formatters.client_formatter import REQUEST_TYPE_LABELS, STATUS_LABELS
from app.common.formatters.property_formatter import PROPERTY_STATUS_LABELS
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
            f"{index}. <b>{client.full_name}</b> · {client.phone} · "
            f"{client.district or '—'} · {status}"
        )

    rows.extend(["", f"Найдено: {len(clients)} (лимит: {limit})."])
    return "\n".join(rows)


def format_property_search_results(properties: list[Property], limit: int) -> str:
    rows = ["<b>Результаты поиска объектов</b>", ""]
    for index, property_obj in enumerate(properties, start=1):
        status = PROPERTY_STATUS_LABELS.get(property_obj.status, property_obj.status.value)
        rows.append(
            f"{index}. <b>{property_obj.title}</b> · {property_obj.district or '—'} · "
            f"{_format_money(property_obj.price)} · {status}"
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
    if filters.get("title"):
        rows.append(f"• Название: {filters['title']}")
    if filters.get("district"):
        rows.append(f"• Район: {filters['district']}")
    if filters.get("property_type"):
        rows.append(f"• Тип: {filters['property_type']}")
    if filters.get("status"):
        rows.append(f"• Статус: {PROPERTY_STATUS_LABELS.get(filters['status'], str(filters['status']))}")
    if filters.get("price_min") is not None:
        rows.append(f"• Цена от: {_format_money(filters['price_min'])}")
    if filters.get("price_max") is not None:
        rows.append(f"• Цена до: {_format_money(filters['price_max'])}")
    if filters.get("rooms") is not None:
        rows.append(f"• Комнаты: {filters['rooms']}")

    return "\n".join(rows)