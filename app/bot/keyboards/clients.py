from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.common.enums import ClientStatus
from app.database.models.client import Client

CANCEL_TEXT = "❌ Отмена"
SKIP_TEXT = "⏭ Пропустить"
ADD_CLIENT_TEXT = "➕ Добавить клиента"
CLIENTS_MENU_TEXT = "👥 Клиенты"
MY_CLIENTS_TEXT = "👤 Мои клиенты"
CLIENTS_BY_STATUS_TEXT = "🧭 По статусу"
RECENT_CLIENTS_TEXT = "🕒 Последние добавленные"

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

STATUS_LABELS: dict[ClientStatus, str] = {
    ClientStatus.NEW: "🆕 Новый",
    ClientStatus.IN_PROGRESS: "🔄 В работе",
    ClientStatus.WAITING: "📞 Ждёт звонка",
    ClientStatus.SHOWING: "🏠 Показ",
    ClientStatus.CLOSED_SUCCESS: "✅ Закрыт",
    ClientStatus.CLOSED_FAILED: "❌ Отказ",
}


def get_clients_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_CLIENT_TEXT)],
            [KeyboardButton(text=MY_CLIENTS_TEXT), KeyboardButton(text=CLIENTS_BY_STATUS_TEXT)],
            [KeyboardButton(text=RECENT_CLIENTS_TEXT)],
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


def get_status_filter_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f"client_status:{status.value}")] for status, label in
            STATUS_LABELS.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_clients_list_inline_keyboard(clients: list[Client]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for client in clients:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{client.id} · {client.full_name}",
                    callback_data=f"client_view:{client.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_client_card_actions_keyboard(client_id: int, can_edit: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if can_edit:
        rows.extend(
            [
                [InlineKeyboardButton(text="✏️ Изменить статус", callback_data=f"client_edit_status:{client_id}")],
                [InlineKeyboardButton(text="📝 Добавить заметку", callback_data=f"client_add_note:{client_id}")],
            ]
        )

    rows.append([InlineKeyboardButton(text="📚 История", callback_data=f"client_history:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_status_change_keyboard(client_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"client_set_status:{client_id}:{status.value}")]
        for status, label in STATUS_LABELS.items()
    ]
    rows.append([InlineKeyboardButton(text="↩️ Назад к карточке", callback_data=f"client_view:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)