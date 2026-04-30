from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import CANCEL_TEXT, get_client_card_actions_keyboard
from app.bot.keyboards.tasks import get_task_cancel_keyboard
from app.bot.states.tasks import TaskCreateStates
from app.common.formatters.client_formatter import format_client_card
from app.common.formatters.task_formatter import format_task_card
from app.common.utils.parsers import build_date_error_message, build_date_prompt, parse_next_contact_at
from app.services.auth_service import AuthService
from app.services.clients import ClientService
from app.services.tasks import TaskService

router = Router(name="task_create")


@router.callback_query(F.data.startswith("client_task_create:"))
async def start_task_create(
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
        await callback.answer("Клиент недоступен", show_alert=True)
        return

    await state.clear()
    await state.set_state(TaskCreateStates.title)
    await state.update_data(client_id=client.id)

    await callback.message.answer(
        "Введите заголовок задачи:",
        reply_markup=get_task_cancel_keyboard(),
    )
    await callback.answer()


@router.message(Command("cancel"), StateFilter(TaskCreateStates))
@router.message(F.text == CANCEL_TEXT, StateFilter(TaskCreateStates))
async def cancel_task_create(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Создание задачи отменено.")


@router.message(TaskCreateStates.title)
async def process_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Заголовок не должен быть пустым. Повторите ввод.")
        return

    await state.update_data(title=title)
    await state.set_state(TaskCreateStates.description)
    await message.answer("Введите описание задачи (или «-», если без описания):")


@router.message(TaskCreateStates.description)
async def process_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    if not description:
        await message.answer("Описание не должно быть пустым. Введите «-», если его нет.")
        return

    await state.update_data(description=None if description == "-" else description)
    await state.set_state(TaskCreateStates.due_at)
    await message.answer(build_date_prompt(label="дату задачи"))


@router.message(TaskCreateStates.due_at)
async def process_due_at(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    task_service: TaskService,
    client_service: ClientService,
    session: AsyncSession,
) -> None:
    due_raw = (message.text or "").strip()
    try:
        due_at = parse_next_contact_at(due_raw)
    except ValueError as error:
        await message.answer(build_date_error_message(error_text=str(error), label="дату задачи"))
        return

    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer("Нет доступа")
        return

    state_data = await state.get_data()
    client_id = state_data.get("client_id")
    title = state_data.get("title")
    if not isinstance(client_id, int) or not isinstance(title, str):
        await state.clear()
        await message.answer("Не удалось завершить создание задачи. Откройте карточку клиента и повторите.")
        return

    try:
        task = await task_service.create_task(
            current_user=user,
            client_id=client_id,
            title=title,
            description=state_data.get("description"),
            due_at=due_at,
        )
    except ValueError as error:
        await state.clear()
        await message.answer(str(error))
        return
    except PermissionError as error:
        await state.clear()
        await message.answer(str(error))
        return

    await session.commit()
    await state.clear()

    await message.answer(format_task_card(task))

    client = await client_service.get_client_for_view(current_user=user, client_id=client_id)
    if client is not None:
        manager_name = client.manager.full_name if client.manager else "—"
        await message.answer(
            format_client_card(client=client, manager_name=manager_name),
            reply_markup=get_client_card_actions_keyboard(
                client_id=client.id,
                can_edit=client_service.can_edit_client(current_user=user, client=client),
            ),
        )