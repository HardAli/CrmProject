from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.clients import CANCEL_TEXT, SKIP_TEXT
from app.common.enums import PropertyStatus, PropertyType
from app.common.utils.phone_links import build_tel_url, build_whatsapp_url
from app.database.models.property import Property

PROPERTIES_MENU_TEXT = "🏠 Объекты"
ADD_PROPERTY_TEXT = "➕ Добавить объект"
MY_PROPERTIES_TEXT = "👤 Мои объекты"
GLOBAL_PROPERTIES_TEXT = "🌐 База объектов"
RECENT_PROPERTIES_TEXT = "🕒 Последние добавленные"
BACK_TO_MAIN_MENU_TEXT = "Главное меню"

PROPERTY_TYPE_OPTIONS: tuple[str, ...] = (
    "Квартира",
    "Дом",
    "Коммерческая",
    "Участок",
)

STATUS_OPTIONS: tuple[str, ...] = (
    "Активен",
    "Продан",
    "Сдан",
    "Архив",
)

PROPERTY_TYPE_MAP: dict[str, PropertyType] = {
    "Квартира": PropertyType.APARTMENT,
    "Дом": PropertyType.HOUSE,
    "Коммерческая": PropertyType.COMMERCIAL,
    "Участок": PropertyType.LAND,
}

PROPERTY_STATUS_MAP: dict[str, PropertyStatus] = {
    "Активен": PropertyStatus.ACTIVE,
    "Продан": PropertyStatus.SOLD,
    "Сдан": PropertyStatus.RESERVED,
    "Архив": PropertyStatus.ARCHIVED,
}


def get_properties_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_PROPERTY_TEXT), KeyboardButton(text=RECENT_PROPERTIES_TEXT)],
            [KeyboardButton(text=MY_PROPERTIES_TEXT), KeyboardButton(text=GLOBAL_PROPERTIES_TEXT)],
            [KeyboardButton(text=BACK_TO_MAIN_MENU_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие с объектами",
    )


def get_property_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите значение или отмените",
    )


def get_property_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите значение или пропустите",
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


def get_property_status_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=STATUS_OPTIONS[0]), KeyboardButton(text=STATUS_OPTIONS[1])],
            [KeyboardButton(text=STATUS_OPTIONS[2]), KeyboardButton(text=STATUS_OPTIONS[3])],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_properties_list_inline_keyboard(properties: list[Property]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for property_obj in properties:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{property_obj.id} · {property_obj.title}",
                    callback_data=f"property_view:{property_obj.id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(text="📞 Позвонить", url=build_tel_url(property_obj.owner_phone)),
            InlineKeyboardButton(text="💬 WhatsApp", url=build_whatsapp_url(property_obj.owner_phone)),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_property_actions_inline_keyboard(property_obj: Property) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📞 Позвонить", url=build_tel_url(property_obj.owner_phone)),
                InlineKeyboardButton(text="💬 WhatsApp", url=build_whatsapp_url(property_obj.owner_phone)),
            ]
        ]
    )