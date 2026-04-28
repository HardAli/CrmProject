from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.common.enums import ClientPropertyRelationStatus, ClientStatus
from app.common.formatters.client_formatter import format_client_compact
from app.common.formatters.property_formatter import format_object_compact
from app.database.models.client import Client
from app.database.models.client_property import ClientProperty
from app.database.models.property import Property

CANCEL_TEXT = "❌ Отмена"
DONE_TEXT = "✅ Готово"
SKIP_TEXT = "⏭ Пропустить"
UNKNOWN_TEXT = "Неизвестно"
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

DISTRICT_OPTIONS: tuple[str, ...] = (
    "Каратал",
    "9-й",
    "Военный городок",
    "Бирлик",
    "Болашак",
    "Гарышкер",
    "Жастар",
    "Жетысу",
    "Коктем",
    "Мушелтой",
    "Самал",
    "Ынтымак",
)

ROOMS_OPTIONS: tuple[str, ...] = ("1", "2", "3", "4", "5", "Студия")
NEXT_CONTACT_QUICK_OPTIONS: tuple[str, ...] = ("Сегодня", "Завтра", "Послезавтра")
WALL_MATERIAL_OPTIONS: tuple[str, ...] = ("Кирпич", "Панель", "Монолит")

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


def get_client_photo_upload_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DONE_TEXT)],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Отправьте фото, затем нажмите «Готово»",
    )


def get_client_create_photo_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DONE_TEXT)],
            [KeyboardButton(text=SKIP_TEXT)],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Отправьте фото или выберите действие",
    )


def get_full_name_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=UNKNOWN_TEXT)], [KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите ФИО или выберите «Неизвестно»",
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


def get_district_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DISTRICT_OPTIONS[0]), KeyboardButton(text=DISTRICT_OPTIONS[1])],
            [KeyboardButton(text=DISTRICT_OPTIONS[2]), KeyboardButton(text=DISTRICT_OPTIONS[3])],
            [KeyboardButton(text=DISTRICT_OPTIONS[4]), KeyboardButton(text=DISTRICT_OPTIONS[5])],
            [KeyboardButton(text=DISTRICT_OPTIONS[6]), KeyboardButton(text=DISTRICT_OPTIONS[7])],
            [KeyboardButton(text=DISTRICT_OPTIONS[8]), KeyboardButton(text=DISTRICT_OPTIONS[9])],
            [KeyboardButton(text=DISTRICT_OPTIONS[10]), KeyboardButton(text=DISTRICT_OPTIONS[11])],
            [KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите район или введите вручную",
    )


def get_rooms_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ROOMS_OPTIONS[0]), KeyboardButton(text=ROOMS_OPTIONS[1]), KeyboardButton(text=ROOMS_OPTIONS[2])],
            [KeyboardButton(text=ROOMS_OPTIONS[3]), KeyboardButton(text=ROOMS_OPTIONS[4]), KeyboardButton(text=ROOMS_OPTIONS[5])],
            [KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите комнаты или введите вручную",
    )


def get_next_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=NEXT_CONTACT_QUICK_OPTIONS[0]), KeyboardButton(text=NEXT_CONTACT_QUICK_OPTIONS[1])],
            [KeyboardButton(text=NEXT_CONTACT_QUICK_OPTIONS[2])],
            [KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите дату или введите вручную",
    )


def get_floor_keyboard() -> ReplyKeyboardMarkup:
    floor_values = [str(value) for value in range(1, 17)]
    rows = [floor_values[i:i + 4] for i in range(0, len(floor_values), 4)]
    keyboard = [[KeyboardButton(text=value) for value in row] for row in rows]
    keyboard.append([KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите этаж 1-16 или введите вручную",
    )


def get_building_floors_keyboard() -> ReplyKeyboardMarkup:
    floor_values = [str(value) for value in range(1, 17)]
    rows = [floor_values[i:i + 4] for i in range(0, len(floor_values), 4)]
    keyboard = [[KeyboardButton(text=value) for value in row] for row in rows]
    keyboard.append([KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите этажность 1-16 или введите вручную",
    )


def get_wall_material_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=WALL_MATERIAL_OPTIONS[0]), KeyboardButton(text=WALL_MATERIAL_OPTIONS[1])],
            [KeyboardButton(text=WALL_MATERIAL_OPTIONS[2])],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите материал стен",
    )


def get_year_built_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=SKIP_TEXT), KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Введите год постройки или пропустите",
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
    first_row: list[InlineKeyboardButton] = [
        InlineKeyboardButton(text="Объекты клиента", callback_data=f"client_properties:{client_id}")
    ]
    second_row: list[InlineKeyboardButton] = [
        InlineKeyboardButton(text="Фото клиента", callback_data=f"client_photos:{client_id}")
    ]

    if can_edit:
        first_row.append(
            InlineKeyboardButton(text="Привязать объект", callback_data=f"client_property_link_pick:{client_id}")
        )
        second_row.append(
            InlineKeyboardButton(text="Изменить статус", callback_data=f"client_edit_status:{client_id}")
        )

    rows.append(first_row)
    rows.append(second_row)

    if can_edit:
        rows.append(
            [
                InlineKeyboardButton(text="Добавить заметку", callback_data=f"client_add_note:{client_id}"),
                InlineKeyboardButton(text="Назначить след. конт.",
                                     callback_data=f"client_set_next_contact:{client_id}"),
            ]
        )
        rows.append([InlineKeyboardButton(text="Создать задачу", callback_data=f"client_task_create:{client_id}")])

    rows.append(
        [
            InlineKeyboardButton(text="Задачи на сегодня", callback_data="tasks_today_dashboard"),
            InlineKeyboardButton(text="История", callback_data=f"client_history:{client_id}"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_client_photos_menu_keyboard(client_id: int, can_manage: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="👀 Показать фото", callback_data=f"client_photo_view:{client_id}")],
    ]
    if can_manage:
        rows.append([InlineKeyboardButton(text="➕ Добавить фото", callback_data=f"client_photo_add:{client_id}")])
        rows.append([InlineKeyboardButton(text="🗑 Удалить фото", callback_data=f"client_photo_delete_menu:{client_id}")])

    rows.append([InlineKeyboardButton(text="↩️ Назад к карточке", callback_data=f"client_view:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_clients_list_keyboard(
    clients: list[Client],
    filters: dict,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for client in clients:
        compact = format_client_compact(client)
        if len(compact) > 60:
            compact = f"{compact[:57]}..."
        rows.append(
            [
                InlineKeyboardButton(
                    text=compact,
                    callback_data=f"client_view:{client.id}",
                )
            ]
        )

    rows.extend(
        [
            [
                InlineKeyboardButton(text="🔎 Поиск", callback_data="clients_search_open"),
                InlineKeyboardButton(text="⚙️ Фильтры", callback_data="clients_filters_open"),
            ],
            [
                InlineKeyboardButton(text="⚡ Быстрые", callback_data="clients_quick_open"),
                InlineKeyboardButton(text="↕️ Сортировка", callback_data="clients_sort_open"),
            ],
            [InlineKeyboardButton(text="🧹 Сброс", callback_data="clients_filters_reset")],
            [
                InlineKeyboardButton(text="⬅️", callback_data="clients_page_prev"),
                InlineKeyboardButton(text=f"{page}/{max(total_pages, 1)}", callback_data="clients_page_info"),
                InlineKeyboardButton(text="➡️", callback_data="clients_page_next"),
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_filters_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Статус", callback_data="clients_filters_status"),
                InlineKeyboardButton(text="Сделка", callback_data="clients_filters_deal"),
            ],
            [
                InlineKeyboardButton(text="Комнаты", callback_data="clients_filters_rooms"),
                InlineKeyboardButton(text="Бюджет", callback_data="clients_filters_budget"),
            ],
            [
                InlineKeyboardButton(text="Район", callback_data="clients_filters_district"),
                InlineKeyboardButton(text="Контакт", callback_data="clients_filters_contact"),
            ],
            [
                InlineKeyboardButton(text="Задачи", callback_data="clients_filters_tasks"),
                InlineKeyboardButton(text="Источник", callback_data="clients_filters_source"),
            ],
            [
                InlineKeyboardButton(text="Объекты", callback_data="clients_filters_objects"),
                InlineKeyboardButton(text="Дополнительно", callback_data="clients_filters_extra"),
            ],
            [InlineKeyboardButton(text="✅ Показать клиентов", callback_data="clients_list_open")],
            [
                InlineKeyboardButton(text="🧹 Сбросить", callback_data="clients_filters_reset"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data="clients_list_open"),
            ],
        ]
    )


def build_status_filter_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    all_statuses = list(ClientStatus)
    for idx in range(0, len(all_statuses), 2):
        row: list[InlineKeyboardButton] = []
        for status in all_statuses[idx:idx + 2]:
            mark = "✅ " if status.value in selected else ""
            row.append(
                InlineKeyboardButton(
                    text=f"{mark}{STATUS_LABELS.get(status, status.value)}",
                    callback_data=f"clients_filter_status_toggle:{status.value}",
                )
            )
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Активные", callback_data="clients_filter_status_active")])
    rows.append([InlineKeyboardButton(text="Все", callback_data="clients_filter_status_all")])
    rows.append([InlineKeyboardButton(text="Готово", callback_data="clients_filters_open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_deal_filter_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    options = [
        ("Покупка", "buy"),
        ("Продажа", "sell"),
        ("Аренда", "rent"),
        ("Сдать в аренду", "rent_out"),
    ]
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅ ' if value in selected else ''}{label}",
                callback_data=f"clients_filter_deal_toggle:{value}",
            )
        ]
        for label, value in options
    ]
    rows.append([InlineKeyboardButton(text="Любой", callback_data="clients_filter_deal_any")])
    rows.append([InlineKeyboardButton(text="Готово", callback_data="clients_filters_open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_rooms_filter_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    options = ("1", "2", "3", "4", "5+", "Студия")
    rows: list[list[InlineKeyboardButton]] = []
    for idx in range(0, len(options), 3):
        row: list[InlineKeyboardButton] = []
        for value in options[idx:idx + 3]:
            row.append(
                InlineKeyboardButton(
                    text=f"{'✅ ' if value in selected else ''}{value}",
                    callback_data=f"clients_filter_rooms_toggle:{value}",
                )
            )
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Любая", callback_data="clients_filter_rooms_any")])
    rows.append([InlineKeyboardButton(text="Готово", callback_data="clients_filters_open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_budget_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="До 15", callback_data="clients_filter_budget_max:15000000"),
                InlineKeyboardButton(text="До 20", callback_data="clients_filter_budget_max:20000000"),
                InlineKeyboardButton(text="До 25", callback_data="clients_filter_budget_max:25000000"),
            ],
            [
                InlineKeyboardButton(text="До 30", callback_data="clients_filter_budget_max:30000000"),
                InlineKeyboardButton(text="До 40", callback_data="clients_filter_budget_max:40000000"),
                InlineKeyboardButton(text="До 50", callback_data="clients_filter_budget_max:50000000"),
            ],
            [InlineKeyboardButton(text="50+", callback_data="clients_filter_budget_min:50000000")],
            [InlineKeyboardButton(text="Любой", callback_data="clients_filter_budget_any")],
            [InlineKeyboardButton(text="Готово", callback_data="clients_filters_open")],
        ]
    )


def build_district_filter_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    options = ("Самал", "Каратал", "6 мкр", "Гарышкер", "Центр", "Жастар", "Мушелтой", "Другие")
    rows: list[list[InlineKeyboardButton]] = []
    for idx in range(0, len(options), 2):
        row: list[InlineKeyboardButton] = []
        for value in options[idx:idx + 2]:
            row.append(
                InlineKeyboardButton(
                    text=f"{'✅ ' if value in selected else ''}{value}",
                    callback_data=f"clients_filter_district_toggle:{value}",
                )
            )
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Любой", callback_data="clients_filter_district_any")])
    rows.append([InlineKeyboardButton(text="Готово", callback_data="clients_filters_open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_contact_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сегодня", callback_data="clients_filter_contact:today")],
            [InlineKeyboardButton(text="Завтра", callback_data="clients_filter_contact:tomorrow")],
            [InlineKeyboardButton(text="Просроченные", callback_data="clients_filter_contact:overdue")],
            [InlineKeyboardButton(text="На неделе", callback_data="clients_filter_contact:week")],
            [InlineKeyboardButton(text="Без даты", callback_data="clients_filter_contact:none")],
            [InlineKeyboardButton(text="Все", callback_data="clients_filter_contact:any")],
            [InlineKeyboardButton(text="Готово", callback_data="clients_filters_open")],
        ]
    )


def build_task_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="На сегодня", callback_data="clients_filter_tasks:today")],
            [InlineKeyboardButton(text="Просроченные", callback_data="clients_filter_tasks:overdue")],
            [InlineKeyboardButton(text="Есть активные", callback_data="clients_filter_tasks:active")],
            [InlineKeyboardButton(text="Без задач", callback_data="clients_filter_tasks:none")],
            [InlineKeyboardButton(text="Выполненные", callback_data="clients_filter_tasks:done")],
            [InlineKeyboardButton(text="Любые", callback_data="clients_filter_tasks:any")],
            [InlineKeyboardButton(text="Готово", callback_data="clients_filters_open")],
        ]
    )


def build_quick_filters_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сегодня связаться", callback_data="clients_quick:today_contact")],
            [InlineKeyboardButton(text="Просроченные контакты", callback_data="clients_quick:overdue_contact")],
            [InlineKeyboardButton(text="Горячие клиенты", callback_data="clients_quick:hot")],
            [InlineKeyboardButton(text="Новые клиенты", callback_data="clients_quick:new")],
            [InlineKeyboardButton(text="Ждут подборку", callback_data="clients_quick:waiting_selection")],
            [InlineKeyboardButton(text="Без след. контакта", callback_data="clients_quick:no_next_contact")],
            [InlineKeyboardButton(text="Без задач", callback_data="clients_quick:no_tasks")],
            [InlineKeyboardButton(text="Отказы", callback_data="clients_quick:failed")],
            [InlineKeyboardButton(text="Закрытые", callback_data="clients_quick:closed")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="clients_list_open")],
        ]
    )


def build_sort_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сначала новые", callback_data="clients_sort:newest")],
            [InlineKeyboardButton(text="Сначала старые", callback_data="clients_sort:oldest")],
            [InlineKeyboardButton(text="Сначала горячие", callback_data="clients_sort:hot_first")],
            [InlineKeyboardButton(text="Ближайший контакт", callback_data="clients_sort:next_contact")],
            [InlineKeyboardButton(text="Просроченные сверху", callback_data="clients_sort:overdue_first")],
            [InlineKeyboardButton(text="По бюджету ↑", callback_data="clients_sort:budget_asc")],
            [InlineKeyboardButton(text="По бюджету ↓", callback_data="clients_sort:budget_desc")],
            [InlineKeyboardButton(text="По имени", callback_data="clients_sort:name")],
            [InlineKeyboardButton(text="Готово", callback_data="clients_list_open")],
        ]
    )


def get_client_photo_delete_keyboard(client_id: int, photos: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for photo_id, label in photos:
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"client_photo_delete:{client_id}:{photo_id}")]
        )

    rows.append([InlineKeyboardButton(text="↩️ К меню фото", callback_data=f"client_photos:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_status_change_keyboard(client_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"client_set_status:{client_id}:{status.value}")]
        for status, label in STATUS_LABELS.items()
    ]
    rows.append([InlineKeyboardButton(text="↩️ Назад к карточке", callback_data=f"client_view:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


RELATION_STATUS_LABELS: dict[ClientPropertyRelationStatus, str] = {
    ClientPropertyRelationStatus.SENT: "📤 Отправлен",
    ClientPropertyRelationStatus.INTERESTED: "🔥 Заинтересовал",
    ClientPropertyRelationStatus.SHOWN: "🏠 Показан",
    ClientPropertyRelationStatus.REJECTED: "❌ Отказался",
    ClientPropertyRelationStatus.IN_NEGOTIATION: "🤝 В переговорах",
    ClientPropertyRelationStatus.DEAL: "✅ Сделка",
}

MAX_PROPERTY_BUTTON_TEXT_LENGTH = 64


def get_client_properties_list_keyboard(*, client_id: int, links: list[ClientProperty],
                                        can_edit: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for link in links:
        status = RELATION_STATUS_LABELS.get(link.relation_status, link.relation_status.value)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{format_object_compact(link.property, max_length=MAX_PROPERTY_BUTTON_TEXT_LENGTH - len(status) - 1)}|{status}",
                    callback_data=f"client_property_view:{link.id}",
                )
            ]
        )

    if can_edit:
        rows.append([InlineKeyboardButton(text="🔗 Привязать объект",
                                          callback_data=f"client_property_link_pick:{client_id}")])
    rows.append([InlineKeyboardButton(text="↩️ Назад к карточке", callback_data=f"client_view:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_property_pick_for_link_keyboard(*, client_id: int, properties: list[Property]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for property_obj in properties:
        rows.append(
            [
                InlineKeyboardButton(
                    text=format_object_compact(property_obj, max_length=MAX_PROPERTY_BUTTON_TEXT_LENGTH),
                    callback_data=f"client_property_link:{client_id}:{property_obj.id}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="↩️ К объектам клиента", callback_data=f"client_properties:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_relation_status_change_keyboard(*, link_id: int, client_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"client_property_set_status:{link_id}:{status.value}",
            )
        ]
        for status, label in RELATION_STATUS_LABELS.items()
    ]
    rows.append(
        [InlineKeyboardButton(text="↩️ К списку объектов клиента", callback_data=f"client_properties:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_client_property_card_keyboard(*, link_id: int, client_id: int, can_edit: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if can_edit:
        rows.append(
            [InlineKeyboardButton(text="🔄 Изменить статус связи",
                                  callback_data=f"client_property_change_status:{link_id}")]
        )
    rows.append([InlineKeyboardButton(text="🏘 Объекты клиента", callback_data=f"client_properties:{client_id}")])
    rows.append([InlineKeyboardButton(text="↩️ Карточка клиента", callback_data=f"client_view:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
