from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Sequence

from app.common.enums import TaskStatus
from app.common.utils.phone_links import format_phone_for_copy
from app.database.models.client import Client
from app.database.models.task import Task

TASK_STATUS_LABELS: dict[TaskStatus, str] = {
    TaskStatus.OPEN: "Открыта",
    TaskStatus.IN_PROGRESS: "В работе",
    TaskStatus.DONE: "Завершена",
    TaskStatus.CANCELED: "Отменена",
}


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def format_task_card(task: Task) -> str:
    client_name = task.client.full_name if task.client else "—"
    assignee = task.assignee.full_name if task.assignee else "—"
    status = TASK_STATUS_LABELS.get(task.status, task.status.value)
    description = escape(task.description) if task.description else "—"
    return (
        f"✅ <b>Задача создана</b>\n\n"
        f"<b>ID:</b> {task.id}\n"
        f"<b>Заголовок:</b> {escape(task.title)}\n"
        f"<b>Описание:</b> {description}\n"
        f"<b>Срок:</b> {_format_datetime(task.due_at)}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Клиент:</b> {escape(client_name)}\n"
        f"<b>Ответственный:</b> {escape(assignee)}"
    )


def format_task_list(tasks: Sequence[Task], *, title: str, limit: int) -> str:
    if not tasks:
        return f"<b>{title}</b>\n\nЗаписей нет."

    rows = [f"<b>{title}</b>", ""]
    for index, task in enumerate(tasks, start=1):
        client_name = task.client.full_name if task.client else "—"
        status = TASK_STATUS_LABELS.get(task.status, task.status.value)
        rows.append(
            f"{index}. #{task.id} {escape(task.title)}\n"
            f"   ⏱ {_format_datetime(task.due_at)} · 👤 {escape(client_name)} · {status}"
        )

    rows.extend(["", f"Показаны первые {min(len(tasks), limit)} записей."])
    return "\n".join(rows)


def format_contacts_list(clients: Sequence[Client], *, title: str, limit: int) -> str:
    if not clients:
        return f"<b>{title}</b>\n\nКлиентов нет."

    rows = [f"<b>{title}</b>", ""]
    for index, client in enumerate(clients, start=1):
        rows.append(
            f"{index}. #{client.id} {escape(client.full_name)}\n"
            f"   Телефон: {format_phone_for_copy(client.phone)}\n"
            f"   📞 {_format_datetime(client.next_contact_at)}"
        )
    rows.extend(["", f"Показаны первые {min(len(clients), limit)} записей."])
    return "\n".join(rows)