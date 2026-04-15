from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.properties import (
    MY_PROPERTIES_TEXT,
    PROPERTIES_MENU_TEXT,
    RECENT_PROPERTIES_TEXT,
    get_properties_list_inline_keyboard,
    get_properties_menu_keyboard,
)
from app.common.enums import UserRole
from app.common.formatters.property_formatter import format_properties_list
from app.services.auth_service import AuthService
from app.services.properties import PropertyService

router = Router(name="property_list")
DEFAULT_LIST_LIMIT = 10


async def _get_current_user(message: Message, auth_service: AuthService):
    telegram_user = message.from_user
    if telegram_user is None:
        await message.answer("Не удалось определить профиль Telegram.")
        return None

    user = await auth_service.get_active_user_by_telegram_id(telegram_user.id)
    if user is None:
        await message.answer("У вас нет доступа к этой функции.")
        return None

    return user


async def _show_properties(message: Message, properties: list, title: str, limit: int) -> None:
    if not properties:
        await message.answer("Объекты не найдены.")
        return

    await message.answer(
        format_properties_list(properties=properties, title=title, limit=limit),
        reply_markup=get_properties_list_inline_keyboard(properties),
    )


@router.message(F.text == PROPERTIES_MENU_TEXT)
async def open_properties_menu(message: Message, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await message.answer("Раздел объектов. Выберите действие:", reply_markup=get_properties_menu_keyboard())


@router.message(F.text == "⬅️ Главное меню")
async def back_to_main_menu(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())


@router.message(F.text == MY_PROPERTIES_TEXT)
async def show_my_properties(message: Message, auth_service: AuthService, property_service: PropertyService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    properties = list(await property_service.get_my_properties(current_user=user, limit=DEFAULT_LIST_LIMIT))
    title = "Мои объекты" if user.role == UserRole.MANAGER else "Все объекты"
    await _show_properties(message, properties, title=title, limit=DEFAULT_LIST_LIMIT)


@router.message(F.text == RECENT_PROPERTIES_TEXT)
async def show_recent_properties(message: Message, auth_service: AuthService, property_service: PropertyService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    properties = list(await property_service.get_recent_properties(current_user=user, limit=DEFAULT_LIST_LIMIT))
    await _show_properties(message, properties, title="Последние добавленные объекты", limit=DEFAULT_LIST_LIMIT)