from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.common.enums import ClientPropertyRelationStatus
from app.common.formatters.property_formatter import PROPERTY_STATUS_LABELS
from app.database.models.client_property import ClientProperty

RELATION_STATUS_LABELS: dict[ClientPropertyRelationStatus, str] = {
    ClientPropertyRelationStatus.SENT: "📤 Отправлен",
    ClientPropertyRelationStatus.INTERESTED: "🔥 Заинтересовал",
    ClientPropertyRelationStatus.SHOWN: "🏠 Показан",
    ClientPropertyRelationStatus.REJECTED: "❌ Отказался",
    ClientPropertyRelationStatus.IN_NEGOTIATION: "🤝 В переговорах",
    ClientPropertyRelationStatus.DEAL: "✅ Сделка",
}


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def format_client_properties_list(links: list[ClientProperty], *, client_name: str, limit: int) -> str:
    rows = [f"<b>Объекты клиента: {client_name}</b>", ""]
    for index, link in enumerate(links, start=1):
        relation_status = RELATION_STATUS_LABELS.get(link.relation_status, link.relation_status.value)
        district = link.property.district or "—"
        rows.append(
            f"{index}. <b>{link.property.title}</b> · {district} · {_format_money(link.property.price)} · {relation_status}"
        )

    rows.extend(["", f"Показаны первые {min(len(links), limit)} записей."])
    return "\n".join(rows)


def format_client_property_link_card(link: ClientProperty) -> str:
    relation_status = RELATION_STATUS_LABELS.get(link.relation_status, link.relation_status.value)
    property_status = PROPERTY_STATUS_LABELS.get(link.property.status, link.property.status.value)
    manager_name = link.property.manager.full_name if link.property.manager else "—"
    return (
        f"<b>Связь клиент ↔ объект #{link.id}</b>\n\n"
        f"<b>ID связи:</b> {link.id}\n"
        f"<b>Клиент:</b> {link.client.full_name} (#{link.client_id})\n"
        f"<b>Объект:</b> {link.property.title} (#{link.property_id})\n"
        f"<b>Статус связи:</b> {relation_status}\n"
        f"<b>Дата привязки:</b> {_format_datetime(link.created_at)}\n\n"
        f"<b>Кратко по объекту</b>\n"
        f"• Название: {link.property.title}\n"
        f"• Район: {link.property.district or '—'}\n"
        f"• Цена: {_format_money(link.property.price)}\n"
        f"• Статус объекта: {property_status}\n"
        f"• Ответственный менеджер: {manager_name}"
    )