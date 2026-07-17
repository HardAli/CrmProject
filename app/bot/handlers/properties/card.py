from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import get_client_card_actions_keyboard
from app.bot.keyboards.properties import (
    get_property_actions_inline_keyboard_with_access,
    get_property_delete_confirm_keyboard,
    get_property_info_keyboard,
)
from app.bot.keyboards.tasks import get_task_cancel_keyboard
from app.bot.states.tasks import TaskCreateStates
from app.bot.utils.chat_ui import send_clean_screen
from app.common.formatters.client_formatter import format_client_card
from app.common.formatters.property_formatter import (
    format_property_card,
    format_property_info_message,
    format_property_public_info_message,
)
from app.services.auth_service import AuthService
from app.services.clients import ClientService
from app.services.properties import PropertyService

router = Router(name="property_card")


@router.callback_query(F.data.startswith("property_view:"))
async def open_property_card(
    callback: CallbackQuery,
    state: FSMContext,
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
    can_edit = property_service.can_edit_property(current_user=user, property_obj=property_obj)
    manager_name = property_obj.manager.full_name if property_obj.manager else "—"
    await send_clean_screen(
        callback,
        state=state,
        scope="property_card",
        text=format_property_card(property_obj=property_obj, manager_name=manager_name),
        reply_markup=get_property_actions_inline_keyboard_with_access(
            property_obj=property_obj,
            can_convert=can_convert,
            can_delete=can_delete,
            can_edit=can_edit,
        ),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_info:"))
async def show_property_info(
    callback: CallbackQuery,
    state: FSMContext,
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
    await send_clean_screen(
        callback,
        state=state,
        scope="property_info",
        text=format_property_info_message(property_obj=property_obj, manager_name=manager_name),
        reply_markup=get_property_info_keyboard(property_id=property_obj.id),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_public_info:"))
async def show_property_public_info(
    callback: CallbackQuery,
    state: FSMContext,
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

    await send_clean_screen(
        callback,
        state=state,
        scope="property_public_info",
        text=format_property_public_info_message(property_obj=property_obj),
        reply_markup=get_property_info_keyboard(property_id=property_obj.id),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_task_create:"))
async def start_task_from_property(
        callback: CallbackQuery,
        state: FSMContext,
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

    try:
        result, client = await property_service.convert_property_to_client(
            current_user=user,
            property_id=int(raw_property_id),
        )
    except PermissionError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    if not client_service.can_edit_client(current_user=user, client=client):
        await session.rollback()
        await callback.answer("Недостаточно прав для создания задачи по этому клиенту", show_alert=True)
        return

    await session.commit()
    await state.clear()
    await state.set_state(TaskCreateStates.title)
    await state.update_data(client_id=client.id)

    prefix = "Клиент создан из объекта." if result == "created" else "Клиент найден по номеру объекта."
    await send_clean_screen(
        callback,
        state=state,
        scope="task_create",
        text=f"{prefix}\n\nВведите заголовок задачи:",
        reply_markup=get_task_cancel_keyboard(),
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_make_client:"))
async def make_client_from_property(
        callback: CallbackQuery,
        state: FSMContext,
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
    await send_clean_screen(
        callback,
        state=state,
        scope="client_card",
        text=prefix + format_client_card(client=client, manager_name=manager_name),
        reply_markup=get_client_card_actions_keyboard(
            client_id=client.id,
            can_edit=client_service.can_edit_client(current_user=user, client=client),
        ),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_delete_confirm:"))
async def ask_property_delete_confirmation(
        callback: CallbackQuery,
        state: FSMContext,
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

    await send_clean_screen(
        callback,
        state=state,
        scope="property_delete_confirm",
        text=f"⚠️ Вы уверены, что хотите удалить объект #{property_obj.id} «{property_obj.title}»?",
        reply_markup=get_property_delete_confirm_keyboard(property_id=property_obj.id),
        parse_mode=None,
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("property_delete_yes:"))
async def delete_property_confirmed(
        callback: CallbackQuery,
        state: FSMContext,
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
    await send_clean_screen(
        callback,
        state=state,
        scope="property_deleted",
        text="✅ Объект удалён. Откройте список объектов, чтобы продолжить работу.",
        prefer_edit=True,
    )
    await callback.answer()
