from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

DATABASE_BUTTON_TEXT = "База"
DATABASE_EXPORT_BUTTON_TEXT = "Выгрузить"
DATABASE_IMPORT_BUTTON_TEXT = "Загрузить"
DATABASE_BACK_BUTTON_TEXT = "Назад"


def get_supervisor_database_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DATABASE_EXPORT_BUTTON_TEXT), KeyboardButton(text=DATABASE_IMPORT_BUTTON_TEXT)],
            [KeyboardButton(text=DATABASE_BACK_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Управление базой данных",
    )