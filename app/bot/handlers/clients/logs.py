from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.utils.chat_ui import send_clean_screen
from app.common.formatters.client_log_formatter import format_client_history
from app.services.auth_service import AuthService
from app.services.clients import ClientService

router = Router(name="client_logs")
DEFAULT_HISTORY_LIMIT = 10


@router.callback_query(F.data.startswith("client_history:"))
async def show_client_history(
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

    try:
        logs = list(
            await client_service.get_client_history(
                current_user=user,
                client_id=int(raw_client_id),
                limit=DEFAULT_HISTORY_LIMIT,
            )
        )
    except ValueError:
        await callback.answer("Клиент не найден или недоступен", show_alert=True)
        return

    await send_clean_screen(
        callback,
        state=state,
        scope="client_history",
        text=format_client_history(logs=logs, limit=DEFAULT_HISTORY_LIMIT),
        prefer_edit=True,
    )
    await callback.answer()
