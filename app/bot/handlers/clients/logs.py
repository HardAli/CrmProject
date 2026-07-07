from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.keyboards.clients import get_client_history_keyboard
from app.bot.utils.chat_ui import send_clean_screen
from app.common.formatters.client_log_formatter import format_client_history
from app.services.auth_service import AuthService
from app.services.clients import ClientService

router = Router(name="client_logs")
DEFAULT_HISTORY_PER_PAGE = 10


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

    parts = callback.data.split(":")
    if len(parts) not in {2, 3}:
        await callback.answer("Некорректная команда", show_alert=True)
        return

    raw_client_id = parts[1]
    raw_page = parts[2] if len(parts) == 3 else "1"
    if not raw_client_id.isdigit() or not raw_page.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    client_id = int(raw_client_id)
    try:
        logs, total_count, page = await client_service.get_client_history_page(
            current_user=user,
            client_id=client_id,
            page=int(raw_page),
            per_page=DEFAULT_HISTORY_PER_PAGE,
        )
    except ValueError:
        await callback.answer("Клиент не найден или недоступен", show_alert=True)
        return

    total_pages = max(1, (total_count + DEFAULT_HISTORY_PER_PAGE - 1) // DEFAULT_HISTORY_PER_PAGE)
    await send_clean_screen(
        callback,
        state=state,
        scope="client_history",
        text=format_client_history(
            logs=logs,
            page=page,
            per_page=DEFAULT_HISTORY_PER_PAGE,
            total_count=total_count,
        ),
        reply_markup=get_client_history_keyboard(client_id=client_id, page=page, total_pages=total_pages),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()
