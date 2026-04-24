from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import get_client_card_actions_keyboard
from app.bot.keyboards.properties import (
    get_property_actions_inline_keyboard_with_access,
    get_property_delete_confirm_keyboard,
)
from app.common.formatters.client_formatter import format_client_card
from app.common.formatters.property_formatter import format_property_card
from app.services.auth_service import AuthService
from app.services.clients import ClientService
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

    can_convert = property_service.can_convert_property(current_user=user, property_obj=property_obj)
    can_delete = property_service.can_delete_property(current_user=user, property_obj=property_obj)
    manager_name = property_obj.manager.full_name if property_obj.manager else "—"
    await callback.message.answer(
        format_property_card(property_obj=property_obj, manager_name=manager_name),
        reply_markup=get_property_actions_inline_keyboard_with_access(
            property_obj=property_obj,
            can_convert=can_convert,
            can_delete=can_delete,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_make_client:"))
async def make_client_from_property(
        callback: CallbackQuery,
        auth_service: AuthService,
        property_service: PropertyService,
        client_service: ClientService,
        session: AsyncSession,
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

    property_id = int(raw_property_id)
    try:
        result, client = await property_service.convert_property_to_client(current_user=user,
                                                                           property_id=property_id)
    except PermissionError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    await session.commit()

    loaded_client = await client_service.get_client_for_view(current_user=user, client_id=client.id)
    if loaded_client is not None:
        client = loaded_client
    manager_name = client.manager.full_name if client.manager else user.full_name
    prefix = "✅ Клиент создан из объекта.\n\n" if result == "created" else "ℹ️ Клиент с таким номером уже существует.\n\n"
    await callback.message.answer(
        prefix + format_client_card(client=client, manager_name=manager_name),
        reply_markup=get_client_card_actions_keyboard(
            client_id=client.id,
            can_edit=client_service.can_edit_client(current_user=user, client=client),
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_delete_confirm:"))
async def ask_property_delete_confirmation(
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
    if not property_service.can_delete_property(current_user=user, property_obj=property_obj):
        await callback.answer("Недостаточно прав для удаления объекта", show_alert=True)
        return

    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить объект #{property_obj.id} «{property_obj.title}»?",
        reply_markup=get_property_delete_confirm_keyboard(property_id=property_obj.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_delete_yes:"))
async def delete_property_confirmed(
        callback: CallbackQuery,
        auth_service: AuthService,
        property_service: PropertyService,
        session: AsyncSession,
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

    try:
        await property_service.delete_property(current_user=user, property_id=int(raw_property_id))
    except PermissionError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    await session.commit()
    await callback.message.answer("✅ Объект удалён. Откройте список объектов, чтобы продолжить работу.")
    await callback.answer()