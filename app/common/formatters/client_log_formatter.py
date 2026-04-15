from __future__ import annotations

from datetime import timezone
from html import escape

from app.common.enums import ClientActionType
from app.database.models.client_log import ClientLog

ACTION_LABELS: dict[ClientActionType, str] = {
    ClientActionType.CLIENT_CREATED: "клиент создан",
    ClientActionType.STATUS_CHANGED: "статус изменён",
    ClientActionType.NOTE_ADDED: "добавлена заметка",
    ClientActionType.CARD_VIEWED: "открыта карточка",
    ClientActionType.TASK_CREATED: "создана задача",
    ClientActionType.NEXT_CONTACT_CHANGED: "изменён следующий контакт",
}


def format_client_history(logs: list[ClientLog], limit: int) -> str:
    if not logs:
        return "История по клиенту пока пустая."

    rows = [f"<b>История действий (последние {limit})</b>", ""]
    for log in logs:
        timestamp = log.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        author = escape(log.user.full_name) if log.user else "Система"
        action = ACTION_LABELS.get(log.action_type, log.action_type.value)
        line = f"• {timestamp} UTC — <b>{author}</b> — {action}"

        if log.comment:
            line += f": {escape(log.comment)}"

        rows.append(line)

    return "\n".join(rows)