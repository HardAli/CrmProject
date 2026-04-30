from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.clients import CANCEL_TEXT, DISTRICT_OPTIONS, ROOMS_OPTIONS, SKIP_TEXT, UNKNOWN_TEXT
from app.bot.keyboards.properties_import import ADD_PROPERTY_BY_LINK_TEXT
from app.common.enums import PropertyStatus, PropertyType
from app.common.formatters.property_formatter import format_object_compact
from app.common.utils.phone_links import build_whatsapp_url
from app.database.models.property import Property

PROPERTIES_MENU_TEXT = "🏠 Объекты"
ADD_PROPERTY_TEXT = "➕ Добавить объект"
MY_PROPERTIES_TEXT = "👤 Мои объекты"
GLOBAL_PROPERTIES_TEXT = "🌐 База объектов"
RECENT_PROPERTIES_TEXT = "🕒 Последние добавленные"
CALL_CAROUSEL_TEXT = "📞 Прозвон"
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
    "Чуж.агенство",
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

MAX_PROPERTY_BUTTON_TEXT_LENGTH = 64
PROPERTY_CREATE_CALLBACK_PREFIX = "prop_create"
MANUAL_INPUT_TEXT = "Ввести вручную"
BACK_TEXT = "⬅️ Назад"
PLAIN_SKIP_TEXT = "Пропустить"


def get_properties_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_PROPERTY_TEXT), KeyboardButton(text=ADD_PROPERTY_BY_LINK_TEXT)],
            [KeyboardButton(text=RECENT_PROPERTIES_TEXT)],
            [KeyboardButton(text=CALL_CAROUSEL_TEXT)],
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


def get_floor_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:1"), InlineKeyboardButton(text="2", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:2"), InlineKeyboardButton(text="3", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:3")],
            [InlineKeyboardButton(text="4", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:4"), InlineKeyboardButton(text="5", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:5"), InlineKeyboardButton(text="6", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:6")],
            [InlineKeyboardButton(text="7", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:7"), InlineKeyboardButton(text="8", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:8"), InlineKeyboardButton(text="9", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:9")],
            [InlineKeyboardButton(text="10+", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:floor:10plus"), InlineKeyboardButton(text="Пропустить", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:skip_floor")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:back"), InlineKeyboardButton(text="❌ Отмена", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:cancel")],
        ]
    )


def get_building_floors_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:1"), InlineKeyboardButton(text="2", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:2"), InlineKeyboardButton(text="3", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:3")],
            [InlineKeyboardButton(text="4", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:4"), InlineKeyboardButton(text="5", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:5"), InlineKeyboardButton(text="6", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:6")],
            [InlineKeyboardButton(text="7", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:7"), InlineKeyboardButton(text="8", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:8"), InlineKeyboardButton(text="9", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:9")],
            [InlineKeyboardButton(text="10", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:10"), InlineKeyboardButton(text="12", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:12"), InlineKeyboardButton(text="16", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:16")],
            [InlineKeyboardButton(text="20+", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_floors:20plus"), InlineKeyboardButton(text="Пропустить", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:skip_building_floors")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:back"), InlineKeyboardButton(text="❌ Отмена", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:cancel")],
        ]
    )


def get_building_year_inline_keyboard() -> InlineKeyboardMarkup:
    years = ("2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016")
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(years), 3):
        rows.append([InlineKeyboardButton(text=year, callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_year:{year}") for year in years[i : i + 3]])
    rows.extend(
        [
            [InlineKeyboardButton(text="Ввести вручную", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_year:manual")],
            [InlineKeyboardButton(text="Пропустить", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:skip_building_year")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:back"), InlineKeyboardButton(text="❌ Отмена", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:cancel")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_building_material_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Кирпич", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Кирпич"), InlineKeyboardButton(text="Панель", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Панель")],
            [InlineKeyboardButton(text="Монолит", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Монолит"), InlineKeyboardButton(text="Пеноблок", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Пеноблок")],
            [InlineKeyboardButton(text="Газоблок", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Газоблок"), InlineKeyboardButton(text="Саман", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Саман")],
            [InlineKeyboardButton(text="Дерево", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Дерево"), InlineKeyboardButton(text="Другое", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:building_material:Другое")],
            [InlineKeyboardButton(text="Пропустить", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:skip_building_material")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:back"), InlineKeyboardButton(text="❌ Отмена", callback_data=f"{PROPERTY_CREATE_CALLBACK_PREFIX}:cancel")],
        ]
    )


def floor_reply_keyboard() -> ReplyKeyboardMarkup:
    floor_values = [str(value) for value in range(1, 17)]
    rows = [floor_values[i:i + 4] for i in range(0, len(floor_values), 4)]
    keyboard = [[KeyboardButton(text=value) for value in row] for row in rows]
    keyboard.append([KeyboardButton(text=MANUAL_INPUT_TEXT), KeyboardButton(text=PLAIN_SKIP_TEXT)])
    keyboard.append([KeyboardButton(text=BACK_TEXT), KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите этаж",
    )


def building_floors_reply_keyboard() -> ReplyKeyboardMarkup:
    floor_values = [str(value) for value in range(1, 17)]
    rows = [floor_values[i:i + 4] for i in range(0, len(floor_values), 4)]
    keyboard = [[KeyboardButton(text=value) for value in row] for row in rows]
    keyboard.append([KeyboardButton(text=MANUAL_INPUT_TEXT), KeyboardButton(text=PLAIN_SKIP_TEXT)])
    keyboard.append([KeyboardButton(text=BACK_TEXT), KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите этажность",
    )


def building_year_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PLAIN_SKIP_TEXT)],
            [KeyboardButton(text=BACK_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Например 1986",
    )


def building_material_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Кирпич"), KeyboardButton(text="Панель")],
            [KeyboardButton(text="Монолит"), KeyboardButton(text="Пеноблок")],
            [KeyboardButton(text="Газоблок"), KeyboardButton(text="Саман")],
            [KeyboardButton(text="Дерево"), KeyboardButton(text="Другое")],
            [KeyboardButton(text=PLAIN_SKIP_TEXT)],
            [KeyboardButton(text=BACK_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Тип строения",
    )


def kitchen_area_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PLAIN_SKIP_TEXT)],
            [KeyboardButton(text=BACK_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Например 10.5",
    )


def get_properties_list_inline_keyboard(properties: list[Property]) -> InlineKeyboardMarkup:
    if not properties:
        return InlineKeyboardMarkup(inline_keyboard=[])

    rows: list[list[InlineKeyboardButton]] = []
    for property_obj in properties:
        property_button = InlineKeyboardButton(
            text=format_object_compact(
                property_obj,
                with_status=False,
                max_length=MAX_PROPERTY_BUTTON_TEXT_LENGTH,
            ),
            callback_data=f"property_view:{property_obj.id}",
        )

        rows.append([property_button])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_property_actions_inline_keyboard(property_obj: Property) -> InlineKeyboardMarkup:
    return get_property_actions_inline_keyboard_with_access(
        property_obj=property_obj,
        can_convert=False,
        can_delete=False,
    )


def get_property_actions_inline_keyboard_with_access(
        *,
        property_obj: Property,
        can_convert: bool,
        can_delete: bool,
        can_edit: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    whatsapp_url = build_whatsapp_url(property_obj.owner_phone)
    if whatsapp_url:
        rows.append([InlineKeyboardButton(text="💬 WhatsApp", url=whatsapp_url)])
    if can_convert:
        rows.append(
            [
                InlineKeyboardButton(
                    text="👤 Сделать клиентом",
                    callback_data=f"property_make_client:{property_obj.id}",
                )
            ]
        )
    if can_edit:
        rows.append([InlineKeyboardButton(text="✏️ Изменить", callback_data=f"property_edit:{property_obj.id}")])
    if can_delete:
        rows.append(
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"property_delete_confirm:{property_obj.id}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_property_delete_confirm_keyboard(*, property_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"property_delete_yes:{property_id}")],
            [InlineKeyboardButton(text="↩️ Отмена", callback_data=f"property_view:{property_id}")],
        ]
    )


def get_duplicate_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, добавить")],
            [KeyboardButton(text="Нет, отмена")],
            [KeyboardButton(text="Открыть найденный объект")],
        ],
        resize_keyboard=True,
    )

PROPERTY_EDIT_CALLBACK_PREFIX = "prop_edit"


def get_property_edit_menu_keyboard(*, property_id: int, is_apartment: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Название", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:title"), InlineKeyboardButton(text="Тип", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:property_type")],
        [InlineKeyboardButton(text="Район", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:district"), InlineKeyboardButton(text="Адрес", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:address")],
        [InlineKeyboardButton(text="Номер", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:owner_phone"), InlineKeyboardButton(text="Цена", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:price")],
        [InlineKeyboardButton(text="Площадь", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:area"), InlineKeyboardButton(text="Кухня", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:kitchen_area")],
        [InlineKeyboardButton(text="Комнаты", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:rooms"), InlineKeyboardButton(text="Описание", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:description")],
        [InlineKeyboardButton(text="Ссылка", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:link"), InlineKeyboardButton(text="Статус", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:status")],
    ]
    if is_apartment:
        rows.extend([
            [InlineKeyboardButton(text="Этаж", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:floor"), InlineKeyboardButton(text="Этажность", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:building_floors")],
            [InlineKeyboardButton(text="Год", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:building_year"), InlineKeyboardButton(text="Материал", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:field:{property_id}:building_material")],
        ])
    rows.append([InlineKeyboardButton(text="👁 Открыть карточку", callback_data=f"property_view:{property_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"property_view:{property_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_property_edit_choice_keyboard(*, property_id: int, field_name: str) -> InlineKeyboardMarkup:
    options_map = {
        "property_type": [("Квартира","Квартира"),("Дом","Дом"),("Коммерческая","Коммерческая"),("Участок","Участок")],
        "district": [(v,v) for v in DISTRICT_OPTIONS_FOR_PROPERTY],
        "rooms": [(v,v) for v in ROOMS_OPTIONS_FOR_PROPERTY],
        "building_material": [("Кирпич","Кирпич"),("Панель","Панель"),("Монолит","Монолит")],
        "status": [("Активен","Активен"),("Продан","Продан"),("Сдан","Сдан"),("Архив","Архив"),("Чуж.агенство","Чуж.агенство")],
    }
    vals = options_map.get(field_name, [])
    rows=[]
    for i in range(0,len(vals),2):
        part=vals[i:i+2]
        rows.append([InlineKeyboardButton(text=t, callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:value:{property_id}:{field_name}:{v}") for t,v in part])
    if field_name in {"floor","building_floors"}:
        nums=[str(x) for x in range(1,17)]
        for i in range(0,len(nums),4):
            part=nums[i:i+4]
            rows.append([InlineKeyboardButton(text=n, callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:value:{property_id}:{field_name}:{n}") for n in part])
    rows.append([InlineKeyboardButton(text="✍️ Ввести вручную", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:manual:{property_id}:{field_name}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{PROPERTY_EDIT_CALLBACK_PREFIX}:menu:{property_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
