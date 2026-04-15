from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.clients import (
    CLIENTS_BY_STATUS_TEXT,
    CLIENTS_MENU_TEXT,
    MY_CLIENTS_TEXT,
    RECENT_CLIENTS_TEXT,
    get_clients_list_inline_keyboard,
    get_clients_menu_keyboard,
    get_status_filter_keyboard,
)
from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.common.enums import ClientStatus
from app.common.formatters.client_formatter import STATUS_LABELS, format_clients_list
from app.services.auth_service import AuthService
from app.services.clients import ClientService

router = Router(name="client_list")
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


async def _show_clients(message: Message, clients: list, title: str, limit: int) -> None:
    if not clients:
        await message.answer("Клиенты не найдены. Попробуйте другой фильтр.")
        return

    text = format_clients_list(clients=clients, title=title, limit=limit)
    await message.answer(text, reply_markup=get_clients_list_inline_keyboard(clients))


@router.message(F.text == CLIENTS_MENU_TEXT)
async def open_clients_menu(message: Message, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await message.answer("Раздел клиентов. Выберите действие:", reply_markup=get_clients_menu_keyboard())


@router.message(F.text == "⬅️ Главное меню")
async def back_to_main_menu(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())


@router.message(F.text == MY_CLIENTS_TEXT)
async def show_my_clients(message: Message, auth_service: AuthService, client_service: ClientService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    clients = list(await client_service.get_my_clients(current_user=user, limit=DEFAULT_LIST_LIMIT))
    await _show_clients(message, clients, title="Мои клиенты", limit=DEFAULT_LIST_LIMIT)


@router.message(F.text == CLIENTS_BY_STATUS_TEXT)
async def show_status_filter(message: Message, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await message.answer("Выберите статус клиента:", reply_markup=get_status_filter_keyboard())


@router.callback_query(F.data.startswith("client_status:"))
async def show_clients_by_status(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_status = callback.data.split(":", maxsplit=1)
    try:
        status = ClientStatus(raw_status)
    except ValueError:
        await callback.answer("Неизвестный статус", show_alert=True)
        return

    clients = list(
        await client_service.get_clients_by_status(
            current_user=user,
            status=status,
            limit=DEFAULT_LIST_LIMIT,
        )
    )
    title = f"Клиенты со статусом: {STATUS_LABELS.get(status, status.value)}"

    if not clients:
        await callback.message.answer("По выбранному статусу клиентов пока нет.")
    else:
        await callback.message.answer(
            format_clients_list(clients=clients, title=title, limit=DEFAULT_LIST_LIMIT),
            reply_markup=get_clients_list_inline_keyboard(clients),
        )

    await callback.answer()


@router.message(F.text == RECENT_CLIENTS_TEXT)
async def show_recent_clients(message: Message, auth_service: AuthService, client_service: ClientService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    clients = list(await client_service.get_recent_clients(current_user=user, limit=DEFAULT_LIST_LIMIT))
    await _show_clients(message, clients, title="Последние добавленные", limit=DEFAULT_LIST_LIMIT)