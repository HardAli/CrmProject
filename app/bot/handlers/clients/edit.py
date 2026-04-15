from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import CANCEL_TEXT, get_cancel_keyboard, get_client_card_actions_keyboard, get_status_change_keyboard
from app.bot.states.clients import ClientCardStates
from app.common.enums import ClientStatus
from app.common.formatters.client_formatter import format_client_card
from app.services.auth_service import AuthService
from app.services.clients import ClientService

router = Router(name="client_edit")


@router.callback_query(F.data.startswith("client_edit_status:"))
async def start_status_change(
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

    _, raw_client_id = callback.data.split(":", maxsplit=1)
    if not raw_client_id.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    client = await client_service.get_client_for_view(current_user=user, client_id=int(raw_client_id))
    if client is None:
        await callback.answer("Клиент не найден или нет доступа", show_alert=True)
        return

    if not client_service.can_edit_client(current_user=user, client=client):
        await callback.answer("У вас нет прав на изменение этого клиента", show_alert=True)
        return

    await callback.message.answer(
        "Выберите новый статус:",
        reply_markup=get_status_change_keyboard(client_id=client.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_set_status:"))
async def set_client_status(
    callback: CallbackQuery,
    auth_service: AuthService,
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

    _, raw_client_id, raw_status = callback.data.split(":", maxsplit=2)
    if not raw_client_id.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    try:
        new_status = ClientStatus(raw_status)
    except ValueError:
        await callback.answer("Некорректный статус", show_alert=True)
        return

    try:
        client = await client_service.change_status(
            current_user=user,
            client_id=int(raw_client_id),
            new_status=new_status,
        )
    except ValueError:
        await callback.answer("Клиент не найден или недоступен", show_alert=True)
        return
    except PermissionError:
        await callback.answer("У вас нет прав на редактирование", show_alert=True)
        return

    await session.commit()

    manager_name = client.manager.full_name if client.manager else "—"
    await callback.message.answer(
        format_client_card(client=client, manager_name=manager_name, updated=True),
        reply_markup=get_client_card_actions_keyboard(
            client_id=client.id,
            can_edit=client_service.can_edit_client(current_user=user, client=client),
        ),
    )
    await callback.answer("Статус обновлён")


@router.callback_query(F.data.startswith("client_add_note:"))
async def start_add_note(
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
        await callback.answer("Клиент не найден или нет доступа", show_alert=True)
        return

    if not client_service.can_edit_client(current_user=user, client=client):
        await callback.answer("У вас нет прав на редактирование", show_alert=True)
        return

    await state.set_state(ClientCardStates.add_note)
    await state.update_data(client_id=client.id)

    await callback.message.answer(
        "Введите новую заметку для клиента (или отмените):",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(Command("cancel"), ClientCardStates.add_note)
@router.message(F.text == CANCEL_TEXT, ClientCardStates.add_note)
async def cancel_add_note(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добавление заметки отменено.")


@router.message(ClientCardStates.add_note)
async def save_note(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
    session: AsyncSession,
) -> None:
    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer("Нет доступа")
        return

    note = (message.text or "").strip()
    if not note:
        await message.answer("Заметка не должна быть пустой. Введите текст или нажмите «Отмена».")
        return

    state_data = await state.get_data()
    client_id = state_data.get("client_id")
    if not isinstance(client_id, int):
        await state.clear()
        await message.answer("Не удалось определить клиента. Попробуйте открыть карточку снова.")
        return

    try:
        client = await client_service.add_note(current_user=user, client_id=client_id, note=note)
    except ValueError:
        await state.clear()
        await message.answer("Клиент не найден или недоступен.")
        return
    except PermissionError:
        await state.clear()
        await message.answer("У вас нет прав на редактирование клиента.")
        return

    await session.commit()
    await state.clear()

    manager_name = client.manager.full_name if client.manager else "—"
    await message.answer(
        format_client_card(client=client, manager_name=manager_name, updated=True),
        reply_markup=get_client_card_actions_keyboard(
            client_id=client.id,
            can_edit=client_service.can_edit_client(current_user=user, client=client),
        ),
    )