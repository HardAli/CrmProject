from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

CANCEL_TEXT = "❌ Отмена"
SKIP_TEXT = "⏭ Пропустить"
ADD_CLIENT_TEXT = "➕ Добавить клиента"
CLIENTS_MENU_TEXT = "👥 Клиенты"

SOURCE_OPTIONS: tuple[str, ...] = (
    "Instagram",
    "WhatsApp",
    "Telegram",
    "Сайт",
    "Реклама",
    "Знакомые",
)

REQUEST_TYPE_OPTIONS: tuple[str, ...] = (
    "Купить",
    "Продать",
    "Снять",
    "Сдать",
)

PROPERTY_TYPE_OPTIONS: tuple[str, ...] = (
    "Квартира",
    "Дом",
    "Коммерческая",
    "Участок",
)


def get_clients_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_CLIENT_TEXT)],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие по клиентам",
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Заполните поле или отмените",
    )


def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите значение или пропустите",
    )


def get_source_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SOURCE_OPTIONS[0]), KeyboardButton(text=SOURCE_OPTIONS[1])],
            [KeyboardButton(text=SOURCE_OPTIONS[2]), KeyboardButton(text=SOURCE_OPTIONS[3])],
            [KeyboardButton(text=SOURCE_OPTIONS[4]), KeyboardButton(text=SOURCE_OPTIONS[5])],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_request_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=REQUEST_TYPE_OPTIONS[0]), KeyboardButton(text=REQUEST_TYPE_OPTIONS[1])],
            [KeyboardButton(text=REQUEST_TYPE_OPTIONS[2]), KeyboardButton(text=REQUEST_TYPE_OPTIONS[3])],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_property_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PROPERTY_TYPE_OPTIONS[0]), KeyboardButton(text=PROPERTY_TYPE_OPTIONS[1])],
            [KeyboardButton(text=PROPERTY_TYPE_OPTIONS[2]), KeyboardButton(text=PROPERTY_TYPE_OPTIONS[3])],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )