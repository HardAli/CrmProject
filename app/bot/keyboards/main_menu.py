from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Клиенты"), KeyboardButton(text="🏠 Объекты")],
            [KeyboardButton(text="✅ Задачи"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔎 Поиск")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )