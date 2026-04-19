from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards.properties import get_property_actions_inline_keyboard
from app.common.formatters.property_formatter import format_property_card
from app.services.auth_service import AuthService
from app.services.properties import PropertyService

router = Router(name="property_card")


@router.callback_query(F.data.startswith("property_view:"))
async def open_property_card(
    callback: CallbackQuery,
    auth_service: AuthService,
    property_service: PropertyService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_property_id = callback.data.split(":", maxsplit=1)
    if not raw_property_id.isdigit():
        await callback.answer("Некорректный ID объекта", show_alert=True)
        return

    property_obj = await property_service.get_property_for_view(current_user=user, property_id=int(raw_property_id))
    if property_obj is None:
        await callback.answer("Объект не найден или нет прав на просмотр", show_alert=True)
        return

    manager_name = property_obj.manager.full_name if property_obj.manager else "—"
    await callback.message.answer(
        format_property_card(property_obj=property_obj, manager_name=manager_name),
        reply_markup=get_property_actions_inline_keyboard(property_obj),
    )
    await callback.answer()
