from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

SUPERVISOR_MENU_COMMAND = "/rol"
USERS_BUTTON_TEXT = "Пользователи"
EXPORT_DB_BUTTON_TEXT = "Выгрузить базу"
MANAGER_PASS_BUTTON_TEXT = "manager pass"
ADMIN_PASS_BUTTON_TEXT = "admin pass"
EXIT_TO_MENU_BUTTON_TEXT = "Выйти в меню"


def get_supervisor_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=USERS_BUTTON_TEXT), KeyboardButton(text=EXPORT_DB_BUTTON_TEXT)],
            [KeyboardButton(text=MANAGER_PASS_BUTTON_TEXT), KeyboardButton(text=ADMIN_PASS_BUTTON_TEXT)],
            [KeyboardButton(text=EXIT_TO_MENU_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Панель supervisor",
    )