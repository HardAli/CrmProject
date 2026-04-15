from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.clients import CANCEL_TEXT

TASKS_MENU_TEXT = "✅ Задачи"
TODAY_TASKS_TEXT = "📅 Задачи на сегодня"
OVERDUE_TASKS_TEXT = "⏰ Просроченные задачи"
TODAY_CONTACTS_TEXT = "📞 Контакты на сегодня"
OVERDUE_CONTACTS_TEXT = "🚨 Просроченные контакты"
MY_TASKS_TEXT = "🗂 Мои задачи"


def get_tasks_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
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