from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from html import escape

from app.common.utils.phone_links import format_phone_for_copy
from app.database.models.client import Client
from app.database.models.task import Task


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone(timezone.utc).strftime("%d.%m %H:%M UTC")


def format_daily_summary(
    *,
    today_tasks_count: int,
    overdue_tasks_count: int,
    today_contacts_count: int,
    overdue_contacts_count: int,
    today_tasks: Sequence[Task],
    overdue_tasks: Sequence[Task],
    today_contacts: Sequence[Client],
    max_items: int = 3,
) -> str:
    rows = [
        "🌅 <b>Утренняя сводка CRM</b>",
        "",
        f"• Задач на сегодня: <b>{today_tasks_count}</b>",
        f"• Просроченных задач: <b>{overdue_tasks_count}</b>",
        f"• Контактов на сегодня: <b>{today_contacts_count}</b>",
        f"• Просроченных контактов: <b>{overdue_contacts_count}</b>",
    ]

    previews: list[str] = []
    if today_tasks:
        previews.append("\n<b>Ближайшие задачи:</b>")
        for index, task in enumerate(today_tasks[:max_items], start=1):
            previews.append(f"{index}. {escape(task.title)} · {_format_dt(task.due_at)}")

    if overdue_tasks:
        previews.append("\n<b>Просроченные задачи:</b>")
        for index, task in enumerate(overdue_tasks[:max_items], start=1):
            previews.append(f"{index}. {escape(task.title)} · {_format_dt(task.due_at)}")

    if today_contacts:
        previews.append("\n<b>Кому связаться сегодня:</b>")
        for index, client in enumerate(today_contacts[:max_items], start=1):
            previews.append(f"{index}. {escape(client.full_name)} · {_format_dt(client.next_contact_at)}")

    return "\n".join(rows + previews)


def format_task_reminder(task: Task) -> str:
    return (
        "⏰ <b>Напоминание по задаче</b>\n\n"
        f"{escape(task.title)}\n"
        f"Срок: {_format_dt(task.due_at)}"
    )


def format_contact_reminder(client: Client) -> str:
    return (
        "📞 <b>Контакт с клиентом</b>\n\n"
        f"{escape(client.full_name)}\n"
        f"Телефон: {format_phone_for_copy(client.phone)}\n"
        f"Время контакта: {_format_dt(client.next_contact_at)}"
    )