from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.common.enums import ClientPropertyRelationStatus, ClientStatus
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
    rows.append([InlineKeyboardButton(text="🏘 Объекты клиента", callback_data=f"client_properties:{client_id}")])
    rows.append([InlineKeyboardButton(text="🖼 Фото клиента", callback_data=f"client_photos:{client_id}")])
    if can_edit:
        rows.extend(
            [
                [InlineKeyboardButton(text="🔗 Привязать объект",
                                      callback_data=f"client_property_link_pick:{client_id}")],
                [InlineKeyboardButton(text="✏️ Изменить статус", callback_data=f"client_edit_status:{client_id}")],
                [InlineKeyboardButton(text="📝 Добавить заметку", callback_data=f"client_add_note:{client_id}")],
                [InlineKeyboardButton(text="📆 Назначить следующий контакт", callback_data=f"client_set_next_contact:{client_id}")],
                [InlineKeyboardButton(text="✅ Создать задачу", callback_data=f"client_task_create:{client_id}")],
            ]
        )

    rows.append([InlineKeyboardButton(text="📅 Задачи на сегодня", callback_data="tasks_today_dashboard")])
    rows.append([InlineKeyboardButton(text="📚 История", callback_data=f"client_history:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_client_photos_menu_keyboard(client_id: int, can_manage: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="👀 Посмотреть фото", callback_data=f"client_photo_view:{client_id}")],
    ]
    if can_manage:
        rows.append([InlineKeyboardButton(text="➕ Добавить фото", callback_data=f"client_photo_add:{client_id}")])
        rows.append([InlineKeyboardButton(text="🗑 Удалить фото", callback_data=f"client_photo_delete_menu:{client_id}")])

    rows.append([InlineKeyboardButton(text="↩️ Назад к карточке", callback_data=f"client_view:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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


def get_client_properties_list_keyboard(*, client_id: int, links: list[ClientProperty],
                                        can_edit: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for link in links:
        status = RELATION_STATUS_LABELS.get(link.relation_status, link.relation_status.value)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{link.id} · {link.property.title} · {status}",
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
                    text=f"#{property_obj.id} · {property_obj.title}",
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