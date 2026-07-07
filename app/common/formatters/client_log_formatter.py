from __future__ import annotations

from datetime import timezone
from html import escape

from app.common.enums import ClientActionType
from app.database.models.client_log import ClientLog

ACTION_LABELS: dict[ClientActionType, str] = {
    ClientActionType.CLIENT_CREATED: "клиент создан",
    ClientActionType.BUYER_REQUEST_CREATED: "создан запрос покупателя",
    ClientActionType.BUYER_REQUEST_STATUS_CHANGED: "статус покупателя изменён",
    ClientActionType.BUYER_PROPERTY_OFFERED: "предложен объект покупателю",
    ClientActionType.STATUS_CHANGED: "статус изменён",
    ClientActionType.NOTE_ADDED: "добавлена заметка",
    ClientActionType.CARD_VIEWED: "открыта карточка",
    ClientActionType.TASK_CREATED: "создана задача",
    ClientActionType.NEXT_CONTACT_CHANGED: "изменён следующий контакт",
}


def format_client_history(
    logs: list[ClientLog],
    *,
    page: int,
    per_page: int,
    total_count: int,
) -> str:
    if not logs:
        return "История по клиенту пока пустая."

    first_item = (page - 1) * per_page + 1
    last_item = min(first_item + len(logs) - 1, total_count)
    rows = [f"История действий · {first_item}-{last_item} из {total_count}", ""]
    for log in logs:
        timestamp = log.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        author = escape(log.user.full_name) if log.user else "Система"
        action = ACTION_LABELS.get(log.action_type, log.action_type.value)
        line = f"• {timestamp} UTC — {author} — {action}"

        if log.comment:
            line += f": {escape(log.comment)}"

        rows.append(line)

    return "\n".join(rows)
