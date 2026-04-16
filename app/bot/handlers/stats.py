from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.stats import (
    SECTION_GLOBAL,
    SECTION_MANAGERS,
    SECTION_PERSONAL,
    SECTION_SOURCES,
    STATS_MENU_TEXT,
    get_stats_sections_keyboard,
    get_stats_view_keyboard,
)
from app.common.dto.statistics import StatsPeriod
from app.common.formatters.stats_formatter import format_lead_sources, format_manager_stats, format_stats_bundle
from app.services.auth_service import AuthService
from app.database.models.user import User
from app.services.statistics import StatisticsService

router = Router(name="statistics")


@router.message(F.text == STATS_MENU_TEXT)
async def open_statistics_menu(
    message: Message,
    auth_service: AuthService,
) -> None:
    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id) if message.from_user else None
    if user is None:
        await message.answer("У вас нет доступа к статистике.")
        return

    default_period = StatsPeriod.DAYS_30
    await message.answer(
        "Выберите раздел статистики:",
        reply_markup=get_stats_sections_keyboard(role=user.role, period=default_period),
    )


@router.callback_query(F.data.startswith("stats:view:"))
async def show_statistics_block(
    callback: CallbackQuery,
    auth_service: AuthService,
    statistics_service: StatisticsService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("У вас нет доступа", show_alert=True)
        return

    section, period = _parse_callback(callback.data)
    if section is None or period is None:
        await callback.answer("Неизвестная команда", show_alert=True)
        return

    try:
        text = await _build_section_text(
            section=section,
            period=period,
            statistics_service=statistics_service,
            user=user,
        )
    except PermissionError as error:
        await callback.answer(str(error), show_alert=True)
        return

    await callback.message.edit_text(
        text,
        reply_markup=get_stats_view_keyboard(role=user.role, section=section, period=period),
    )
    await callback.answer()


async def _build_section_text(
    *,
    section: str,
    period: StatsPeriod,
    statistics_service: StatisticsService,
    user: User,
) -> str:
    if section == SECTION_PERSONAL:
        personal_stats = await statistics_service.get_personal_stats(current_user=user, period=period)
        return format_stats_bundle(title="Моя статистика", period=period, stats=personal_stats)

    if section == SECTION_GLOBAL:
        global_stats = await statistics_service.get_global_stats(current_user=user, period=period)
        return format_stats_bundle(title="Общая статистика", period=period, stats=global_stats)

    if section == SECTION_SOURCES:
        lead_stats = await statistics_service.get_lead_source_stats(current_user=user, period=period)
        return format_lead_sources(period=period, stats=lead_stats)

    if section == SECTION_MANAGERS:
        manager_rows = await statistics_service.get_manager_stats(current_user=user, period=period)
        return format_manager_stats(period=period, rows=manager_rows)

    raise PermissionError("Раздел статистики не найден")


def _parse_callback(data: str | None) -> tuple[str | None, StatsPeriod | None]:
    if not data:
        return None, None

    parts = data.split(":")
    if len(parts) != 4:
        return None, None

    _, _, section, period_value = parts
    try:
        period = StatsPeriod(period_value)
    except ValueError:
        return None, None

    return section, period