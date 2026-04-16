from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.clients import CANCEL_TEXT, SKIP_TEXT

SEARCH_MENU_TEXT = "🔎 Поиск"
SEARCH_CLIENTS_TEXT = "👥 Поиск клиентов"
SEARCH_PROPERTIES_TEXT = "🏠 Поиск объектов"
QUICK_SEARCH_TEXT = "⚡ Быстрый поиск"
ADVANCED_SEARCH_TEXT = "🧩 Расширенный поиск"
RUN_SEARCH_TEXT = "🔍 Выполнить поиск"


def get_search_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SEARCH_CLIENTS_TEXT), KeyboardButton(text=SEARCH_PROPERTIES_TEXT)],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Что ищем?",
    )


def get_search_mode_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=QUICK_SEARCH_TEXT), KeyboardButton(text=ADVANCED_SEARCH_TEXT)],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите режим поиска",
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


def get_search_results_hint_keyboard(entity: str) -> InlineKeyboardMarkup:
    callback_data = "search_open_clients" if entity == "clients" else "search_open_properties"
    text = "↩️ Новый поиск клиентов" if entity == "clients" else "↩️ Новый поиск объектов"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback_data)]])