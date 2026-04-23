from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.clients import CANCEL_TEXT, DISTRICT_OPTIONS, ROOMS_OPTIONS, SKIP_TEXT, UNKNOWN_TEXT
from app.bot.keyboards.properties_import import ADD_PROPERTY_BY_LINK_TEXT
from app.common.enums import PropertyStatus, PropertyType
from app.common.utils.phone_links import build_whatsapp_url
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

DISTRICT_OPTIONS_FOR_PROPERTY: tuple[str, ...] = DISTRICT_OPTIONS
ROOMS_OPTIONS_FOR_PROPERTY: tuple[str, ...] = ROOMS_OPTIONS

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
            [KeyboardButton(text=ADD_PROPERTY_TEXT), KeyboardButton(text=ADD_PROPERTY_BY_LINK_TEXT)],
            [KeyboardButton(text=RECENT_PROPERTIES_TEXT)],
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


def get_property_title_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=UNKNOWN_TEXT)], [KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите название или выберите «Неизвестно»",
    )


def get_property_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите значение или пропустите",
    )


def get_property_district_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[0]), KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[1])],
            [KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[2]), KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[3])],
            [KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[4]), KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[5])],
            [KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[6]), KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[7])],
            [KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[8]), KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[9])],
            [KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[10]), KeyboardButton(text=DISTRICT_OPTIONS_FOR_PROPERTY[11])],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите район или введите вручную",
    )


def get_property_rooms_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ROOMS_OPTIONS_FOR_PROPERTY[0]), KeyboardButton(text=ROOMS_OPTIONS_FOR_PROPERTY[1]), KeyboardButton(text=ROOMS_OPTIONS_FOR_PROPERTY[2])],
            [KeyboardButton(text=ROOMS_OPTIONS_FOR_PROPERTY[3]), KeyboardButton(text=ROOMS_OPTIONS_FOR_PROPERTY[4]), KeyboardButton(text=ROOMS_OPTIONS_FOR_PROPERTY[5])],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите комнаты или введите вручную",
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
    if not properties:
        return InlineKeyboardMarkup(inline_keyboard=[])

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

    rows.append([InlineKeyboardButton(text="💬 WhatsApp", url=build_whatsapp_url(properties[-1].owner_phone))])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_property_actions_inline_keyboard(property_obj: Property) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 WhatsApp", url=build_whatsapp_url(property_obj.owner_phone))]
        ]
    )
