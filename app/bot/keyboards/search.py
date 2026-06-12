from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.clients import CANCEL_TEXT, SKIP_TEXT
from app.common.formatters.buyer_request_formatter import BUYER_STATUS_LABELS

SEARCH_MENU_TEXT = "🔎 Поиск"
QUICK_CLIENT_SEARCH_TEXT = "⚡ Быстрый Клиент"
QUICK_BUYER_SEARCH_TEXT = "⚡ Быстрый Покупатель"
QUICK_PROPERTY_SEARCH_TEXT = "⚡ Быстрый Объект"
ADVANCED_CLIENT_SEARCH_TEXT = "🧩 Расширенный Клиент"
ADVANCED_BUYER_SEARCH_TEXT = "🧩 Расширенный Покупатель"
ADVANCED_PROPERTY_SEARCH_TEXT = "🧩 Расширенный Объект"
RUN_SEARCH_TEXT = "🔍 Выполнить поиск"


def get_search_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=QUICK_CLIENT_SEARCH_TEXT), KeyboardButton(text=QUICK_BUYER_SEARCH_TEXT)],
            [KeyboardButton(text=QUICK_PROPERTY_SEARCH_TEXT)],
            [KeyboardButton(text=ADVANCED_CLIENT_SEARCH_TEXT), KeyboardButton(text=ADVANCED_BUYER_SEARCH_TEXT)],
            [KeyboardButton(text=ADVANCED_PROPERTY_SEARCH_TEXT)],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите формат поиска",
    )


def get_search_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите данные или отмените",
    )


def get_search_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите значение или пропустите",
    )


def get_client_search_status_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Новый"), KeyboardButton(text="В работе")],
            [KeyboardButton(text="Ждёт звонка"), KeyboardButton(text="Показ")],
            [KeyboardButton(text="Закрыт"), KeyboardButton(text="Отказ")],
            [KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_client_search_request_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Купить"), KeyboardButton(text="Продать")],
            [KeyboardButton(text="Снять"), KeyboardButton(text="Сдать")],
            [KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_buyer_search_status_keyboard() -> ReplyKeyboardMarkup:
    labels = list(BUYER_STATUS_LABELS.values())
    rows = [
        [KeyboardButton(text=label) for label in labels[index:index + 2]]
        for index in range(0, len(labels), 2)
    ]
    rows.append([KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_property_search_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Квартира"), KeyboardButton(text="Дом")],
            [KeyboardButton(text="Коммерческая"), KeyboardButton(text="Участок")],
            [KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_property_search_status_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Активен"), KeyboardButton(text="Продан")],
            [KeyboardButton(text="Сдан"), KeyboardButton(text="Архив")],
            [KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )
