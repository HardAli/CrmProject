from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import CANCEL_TEXT, get_client_card_actions_keyboard
from app.bot.keyboards.tasks import (
    CREATE_TASK_TEXT,
    get_task_cancel_keyboard,
    get_task_card_actions_keyboard,
    get_task_client_pick_keyboard,
)
from app.bot.states.tasks import TaskCreateStates
from app.bot.utils.chat_ui import send_clean_bundle, send_clean_screen
from app.common.formatters.client_formatter import format_client_card
from app.common.formatters.task_formatter import format_task_card
from app.common.utils.parsers import build_date_error_message, build_date_prompt, parse_next_contact_at
from app.services.auth_service import AuthService
from app.services.clients import ClientService
from app.services.tasks import TaskService

router = Router(name="task_create")
CLIENT_PICK_LIMIT = 10


async def _show_task_create_step(
    target: Message | CallbackQuery,
    state: FSMContext,
    text: str,
    *,
    reply_markup=None,
    scope: str = "task_create",
) -> None:
    await send_clean_screen(
        target,
        state=state,
        scope=scope,
        text=text,
        reply_markup=reply_markup,
        prefer_edit=isinstance(target, CallbackQuery),
    )


@router.message(F.text == CREATE_TASK_TEXT)
async def open_task_client_picker(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить профиль Telegram.")
        return

    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("У вас нет доступа к этой функции.")
        return

    clients = list(await client_service.get_my_clients(current_user=user, limit=CLIENT_PICK_LIMIT))
    await state.clear()
    if not clients:
        await _show_task_create_step(
            message,
            state,
            "Клиенты не найдены. Сначала добавьте клиента, затем создайте задачу.",
            scope="task_client_pick_empty",
        )
        return

    await _show_task_create_step(
        message,
        state,
        "Выберите клиента для задачи:",
        reply_markup=get_task_client_pick_keyboard(clients),
        scope="task_client_pick",
    )


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

    await _show_task_create_step(
        callback,
        state,
        "Введите заголовок задачи:",
        reply_markup=get_task_cancel_keyboard(),
    )
    await callback.answer()


@router.message(Command("cancel"), StateFilter(TaskCreateStates))
@router.message(F.text == CANCEL_TEXT, StateFilter(TaskCreateStates))
async def cancel_task_create(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _show_task_create_step(message, state, "Создание задачи отменено.", scope="task_create_cancelled")


@router.message(TaskCreateStates.title)
async def process_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await _show_task_create_step(message, state, "Заголовок не должен быть пустым. Повторите ввод.", reply_markup=get_task_cancel_keyboard())
        return

    await state.update_data(title=title)
    await state.set_state(TaskCreateStates.description)
    await _show_task_create_step(message, state, "Введите описание задачи (или «-», если без описания):", reply_markup=get_task_cancel_keyboard())


@router.message(TaskCreateStates.description)
async def process_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    if not description:
        await _show_task_create_step(message, state, "Описание не должно быть пустым. Введите «-», если его нет.", reply_markup=get_task_cancel_keyboard())
        return

    await state.update_data(description=None if description == "-" else description)
    await state.set_state(TaskCreateStates.due_at)
    await _show_task_create_step(message, state, build_date_prompt(label="дату задачи"), reply_markup=get_task_cancel_keyboard())


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
        await _show_task_create_step(message, state, build_date_error_message(error_text=str(error), label="дату задачи"), reply_markup=get_task_cancel_keyboard())
        return

    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await _show_task_create_step(message, state, "Нет доступа", scope="task_create_error")
        return

    state_data = await state.get_data()
    client_id = state_data.get("client_id")
    title = state_data.get("title")
    if not isinstance(client_id, int) or not isinstance(title, str):
        await state.clear()
        await _show_task_create_step(message, state, "Не удалось завершить создание задачи. Откройте карточку клиента и повторите.", scope="task_create_error")
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
        await _show_task_create_step(message, state, str(error), scope="task_create_error")
        return
    except PermissionError as error:
        await state.clear()
        await _show_task_create_step(message, state, str(error), scope="task_create_error")
        return

    await session.commit()
    await state.clear()

    client = await client_service.get_client_for_view(current_user=user, client_id=client_id)
    if client is not None:
        manager_name = client.manager.full_name if client.manager else "—"
        await send_clean_bundle(
            message,
            state=state,
            items=[
                {
                    "scope": "task_card",
                    "text": format_task_card(task, created=True),
                    "reply_markup": get_task_card_actions_keyboard(task),
                },
                {
                    "scope": "client_card",
                    "text": format_client_card(client=client, manager_name=manager_name),
                    "reply_markup": get_client_card_actions_keyboard(
                        client_id=client.id,
                        can_edit=client_service.can_edit_client(current_user=user, client=client),
                    ),
                    "parse_mode": "HTML",
                },
            ],
        )
        return

    await _show_task_create_step(
        message,
        state,
        format_task_card(task, created=True),
        reply_markup=get_task_card_actions_keyboard(task),
        scope="task_card",
    )
