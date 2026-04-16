from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.common.dto.statistics import StatsPeriod
from app.common.enums import UserRole

STATS_MENU_TEXT = "📊 Статистика"

SECTION_PERSONAL = "personal"
SECTION_GLOBAL = "global"
SECTION_MANAGERS = "managers"
SECTION_SOURCES = "sources"

SECTION_LABELS: dict[str, str] = {
    SECTION_PERSONAL: "📈 Моя статистика",
    SECTION_GLOBAL: "🌍 Общая статистика",
    SECTION_MANAGERS: "👥 По менеджерам",
    SECTION_SOURCES: "📥 По источникам лидов",
}

PERIOD_LABELS: dict[StatsPeriod, str] = {
    StatsPeriod.TODAY: "Сегодня",
    StatsPeriod.DAYS_30: "30 дней",
    StatsPeriod.ALL_TIME: "Всё время",
}


def get_stats_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=STATS_MENU_TEXT)],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Откройте статистику",
    )


def get_stats_sections_keyboard(*, role: UserRole, period: StatsPeriod) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_build_section_rows(role=role, period=period))


def get_stats_view_keyboard(*, role: UserRole, section: str, period: StatsPeriod) -> InlineKeyboardMarkup:
    period_row: list[InlineKeyboardButton] = []
    for p in (StatsPeriod.TODAY, StatsPeriod.DAYS_30, StatsPeriod.ALL_TIME):
        label = PERIOD_LABELS[p]
        if p == period:
            label = f"✅ {label}"
        period_row.append(InlineKeyboardButton(text=label, callback_data=_build_callback(section, p)))

    return InlineKeyboardMarkup(inline_keyboard=[period_row, *_build_section_rows(role=role, period=period)])


def _build_section_rows(*, role: UserRole, period: StatsPeriod) -> list[list[InlineKeyboardButton]]:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=SECTION_LABELS[SECTION_PERSONAL], callback_data=_build_callback(SECTION_PERSONAL, period))]
    ]

    if role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
        rows.append([InlineKeyboardButton(text=SECTION_LABELS[SECTION_GLOBAL], callback_data=_build_callback(SECTION_GLOBAL, period))])
        rows.append([InlineKeyboardButton(text=SECTION_LABELS[SECTION_SOURCES], callback_data=_build_callback(SECTION_SOURCES, period))])
        rows.append([InlineKeyboardButton(text=SECTION_LABELS[SECTION_MANAGERS], callback_data=_build_callback(SECTION_MANAGERS, period))])

    return rows


def _build_callback(section: str, period: StatsPeriod) -> str:
    return f"stats:view:{section}:{period.value}"