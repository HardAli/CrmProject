from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.common.enums import TaskStatus
from app.common.formatters.client_formatter import format_client_compact
from app.database.models.client import Client
from app.database.models.task import Task

from app.bot.keyboards.clients import CANCEL_TEXT

TASKS_MENU_TEXT = "✅ Задачи"
CREATE_TASK_TEXT = "➕ Создать задачу"
TODAY_TASKS_TEXT = "📅 Задачи на сегодня"
OVERDUE_TASKS_TEXT = "⏰ Просроченные задачи"
TODAY_CONTACTS_TEXT = "📞 Контакты на сегодня"
OVERDUE_CONTACTS_TEXT = "🚨 Просроченные контакты"
MY_TASKS_TEXT = "🗂 Мои задачи"


def get_tasks_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CREATE_TASK_TEXT)],
            [KeyboardButton(text=TODAY_TASKS_TEXT), KeyboardButton(text=OVERDUE_TASKS_TEXT)],
            [KeyboardButton(text=TODAY_CONTACTS_TEXT), KeyboardButton(text=OVERDUE_CONTACTS_TEXT)],
            [KeyboardButton(text=MY_TASKS_TEXT)],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие с задачами",
    )


def get_task_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите значение или отмените",
    )


def get_task_client_pick_keyboard(clients: list[Client]) -> InlineKeyboardMarkup | None:
    if not clients:
        return None

    rows: list[list[InlineKeyboardButton]] = []
    for client in clients:
        prefix = f"#{client.id} · "
        compact = format_client_compact(client)
        max_compact_length = max(1, 64 - len(prefix))
        if len(compact) > max_compact_length:
            compact = f"{compact[:max(1, max_compact_length - 3)]}..."
        rows.append([InlineKeyboardButton(text=f"{prefix}{compact}", callback_data=f"client_task_create:{client.id}")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_task_list_inline_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup | None:
    if not tasks:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Открыть #{task.id}: {task.title[:24]}", callback_data=f"task_open:{task.id}")]
            for task in tasks
        ]
    )


def get_task_reminder_keyboard(task: Task, *, completed: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if not completed and task.status not in {TaskStatus.DONE, TaskStatus.CANCELED}:
        rows.append([InlineKeyboardButton(text="✅ Завершена", callback_data=f"task_complete:{task.id}")])

    rows.append(
        [
            InlineKeyboardButton(text="📌 Карточка задачи", callback_data=f"task_open:{task.id}"),
            InlineKeyboardButton(text="👤 Карточка клиента", callback_data=f"client_view:{task.client_id}"),
        ]
    )
    rows.append([InlineKeyboardButton(text="🗂 Все задачи", callback_data="tasks_all")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_contact_reminder_keyboard(client: Client, *, completed: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if not completed:
        rows.append([InlineKeyboardButton(text="✅ Завершена", callback_data=f"contact_done:{client.id}")])

    rows.append(
        [
            InlineKeyboardButton(text="📌 Карточка задачи", callback_data=f"contact_task_card:{client.id}"),
            InlineKeyboardButton(text="👤 Карточка клиента", callback_data=f"client_view:{client.id}"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(text="🗂 Все задачи", callback_data="tasks_all"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_task_card_actions_keyboard(task: Task) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if task.status not in {TaskStatus.DONE, TaskStatus.CANCELED}:
        rows.append([InlineKeyboardButton(text="✅ Завершена", callback_data=f"task_complete:{task.id}")])

    rows.append(
        [
            InlineKeyboardButton(text="👤 Карточка клиента", callback_data=f"client_view:{task.client_id}"),
            InlineKeyboardButton(text="🗂 Все задачи", callback_data="tasks_all"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
