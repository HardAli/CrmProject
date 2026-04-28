from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.common.utils.phone_links import build_tel_url, build_whatsapp_url


CALL_MODE_DEFAULT = "default"
CALL_MODE_RETRY = "retry"
CALL_MODE_NEW = "new"
CALL_MODE_MY = "my"


def get_call_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Начать прозвон", callback_data=f"callstart:{CALL_MODE_DEFAULT}")],
            [InlineKeyboardButton(text="🔁 Повторный прозвон", callback_data=f"callstart:{CALL_MODE_RETRY}")],
            [InlineKeyboardButton(text="🆕 Новые объекты", callback_data=f"callstart:{CALL_MODE_NEW}")],
            [InlineKeyboardButton(text="👤 Мои объекты", callback_data=f"callstart:{CALL_MODE_MY}")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="callstats")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="callmenu_exit")],
        ]
    )


def get_call_card_keyboard(*, property_id: int, phone: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    tel_url = build_tel_url(phone)
    wa_url = build_whatsapp_url(phone)
    if tel_url:
        rows.append([InlineKeyboardButton(text="📞 Позвонить", url=tel_url)])

    second_row: list[InlineKeyboardButton] = []
    if wa_url:
        second_row.append(InlineKeyboardButton(text="💬 WhatsApp", url=wa_url))
    if tel_url:
        second_row.append(InlineKeyboardButton(text="📋 Номер", callback_data=f"callcopy:{property_id}"))
    if second_row:
        rows.append(second_row)

    rows.extend(
        [
            [
                InlineKeyboardButton(text="✅ Договорился", callback_data=f"callres:{property_id}:agreed"),
            ],
            [
                InlineKeyboardButton(text="📵 Недозвон", callback_data=f"callres:{property_id}:no_answer"),
                InlineKeyboardButton(text="❌ Отказ", callback_data=f"callres:{property_id}:rejected"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Ещё", callback_data=f"callmore:{property_id}"),
                InlineKeyboardButton(text="⏭ Следующий", callback_data=f"callnext:{property_id}"),
            ],
            [
                InlineKeyboardButton(text="⏸ Пауза", callback_data="callpause"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data="callmenu"),
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_call_more_keyboard(property_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Заметка", callback_data=f"callnote:{property_id}")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"callprice:{property_id}")],
            [InlineKeyboardButton(text="🏁 Продано", callback_data=f"callsold:{property_id}")],
            [InlineKeyboardButton(text="📄 Карточка", callback_data=f"callcard:{property_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к прозвону", callback_data=f"callbacktocard:{property_id}")],
        ]
    )


def get_no_answer_keyboard(property_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Через 2 часа", callback_data=f"callnoans:{property_id}:2h"),
                InlineKeyboardButton(text="Сегодня вечером", callback_data=f"callnoans:{property_id}:evening"),
            ],
            [
                InlineKeyboardButton(text="Завтра", callback_data=f"callnoans:{property_id}:tomorrow"),
                InlineKeyboardButton(text="Через 3 дня", callback_data=f"callnoans:{property_id}:3d"),
            ],
            [InlineKeyboardButton(text="Без даты", callback_data=f"callnoans:{property_id}:none")],
        ]
    )


def get_reject_reason_keyboard(property_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Не сотрудничает", callback_data=f"callrej:{property_id}:no_cooperation"),
                InlineKeyboardButton(text="Не актуально", callback_data=f"callrej:{property_id}:not_actual"),
            ],
            [
                InlineKeyboardButton(text="Не тот номер", callback_data=f"callrej:{property_id}:wrong_number"),
                InlineKeyboardButton(text="Другое", callback_data=f"callrej:{property_id}:other"),
            ],
            [
                InlineKeyboardButton(text="Просто отказ", callback_data=f"callrej:{property_id}:skip"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"callbacktocard:{property_id}"),
            ],
        ]
    )


def get_sold_confirm_keyboard(property_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, продано", callback_data=f"callsold_confirm:{property_id}"),
                InlineKeyboardButton(text="Отмена", callback_data=f"callsold_cancel:{property_id}"),
            ]
        ]
    )


def get_note_cancel_keyboard(property_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=f"callbacktocard:{property_id}")]]
    )


def get_call_finished_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Повторный прозвон", callback_data=f"callstart:{CALL_MODE_RETRY}")],
            [InlineKeyboardButton(text="▶️ Начать заново", callback_data=f"callstart:{CALL_MODE_DEFAULT}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="callmenu")],
        ]
    )
