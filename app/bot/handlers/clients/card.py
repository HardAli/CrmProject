from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.keyboards.clients import get_client_card_actions_keyboard, get_client_info_keyboard
from app.bot.utils.chat_ui import send_clean_screen
from app.common.formatters.client_formatter import format_client_card, format_client_info_message
from app.services.auth_service import AuthService
from app.services.clients import ClientService

router = Router(name="client_card")


@router.callback_query(F.data.startswith("client_view:"))
async def open_client_card(
    callback: CallbackQuery,
    state: FSMContext,
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

    _, raw_client_id = callback.data.split(":", maxsplit=1)
    if not raw_client_id.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    client = await client_service.get_client_for_view(current_user=user, client_id=int(raw_client_id))
    if client is None:
        await callback.answer("Клиент не найден или нет прав на просмотр", show_alert=True)
        return

    manager_name = client.manager.full_name if client.manager else "—"
    await send_clean_screen(
        callback,
        state=state,
        scope="client_card",
        text=format_client_card(client=client, manager_name=manager_name),
        reply_markup=get_client_card_actions_keyboard(
            client_id=client.id,
            can_edit=client_service.can_edit_client(current_user=user, client=client),
        ),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_info:"))
async def show_client_info(
    callback: CallbackQuery,
    state: FSMContext,
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

    _, raw_client_id = callback.data.split(":", maxsplit=1)
    if not raw_client_id.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    client = await client_service.get_client_for_view(current_user=user, client_id=int(raw_client_id))
    if client is None:
        await callback.answer("Клиент не найден или нет прав на просмотр", show_alert=True)
        return

    manager_name = client.manager.full_name if client.manager else "—"
    await send_clean_screen(
        callback,
        state=state,
        scope="client_info",
        text=format_client_info_message(client=client, manager_name=manager_name),
        reply_markup=get_client_info_keyboard(client_id=client.id),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()
