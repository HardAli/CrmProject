from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.clients import CANCEL_TEXT

ADD_PROPERTY_BY_LINK_TEXT = "🔗 Добавить по ссылке"
SAVE_IMPORTED_PROPERTY_TEXT = "✅ Сохранить"
FILL_MISSING_FIELDS_TEXT = "✍️ Заполнить недостающие поля"


def get_property_import_url_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Отправьте ссылку на объявление",
    )


def get_property_import_preview_keyboard(*, has_missing_fields: bool) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=SAVE_IMPORTED_PROPERTY_TEXT), KeyboardButton(text=CANCEL_TEXT)]]
    if has_missing_fields:
        rows.insert(0, [KeyboardButton(text=FILL_MISSING_FIELDS_TEXT)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)