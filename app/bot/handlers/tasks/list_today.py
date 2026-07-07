from __future__ import annotations

from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.tasks import (
    MY_TASKS_TEXT,
    OVERDUE_CONTACTS_TEXT,
    OVERDUE_TASKS_TEXT,
    TASKS_MENU_TEXT,
    TODAY_CONTACTS_TEXT,
    TODAY_TASKS_TEXT,
    get_contact_reminder_keyboard,
    get_task_card_actions_keyboard,
    get_task_list_inline_keyboard,
    get_task_reminder_keyboard,
    get_tasks_menu_keyboard,
)
from app.bot.utils.chat_ui import send_clean_screen
from app.common.formatters.task_formatter import format_contacts_list, format_task_card, format_task_list
from app.services.auth_service import AuthService
from app.services.clients import ClientService
from app.services.tasks import TaskService

router = Router(name="tasks_list")
DEFAULT_TASK_LIMIT = 15


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


@router.message(F.text == TASKS_MENU_TEXT)
async def open_tasks_menu(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await send_clean_screen(message, state=state, scope="tasks_menu", text="Раздел задач. Выберите действие:", reply_markup=get_tasks_menu_keyboard(), prefer_edit=False)


@router.callback_query(F.data == "tasks_today_dashboard")
async def show_dashboard_from_client_card(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    task_service: TaskService,
    client_service: ClientService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    today_tasks = list(await task_service.get_today_tasks(current_user=user, limit=DEFAULT_TASK_LIMIT))
    overdue_tasks = list(await task_service.get_overdue_tasks(current_user=user, limit=DEFAULT_TASK_LIMIT))
    today_contacts = list(await client_service.get_today_contacts(current_user=user, limit=DEFAULT_TASK_LIMIT))
    overdue_contacts = list(await client_service.get_overdue_contacts(current_user=user, limit=DEFAULT_TASK_LIMIT))

    await send_clean_screen(
        callback,
        state=state,
        scope="tasks_dashboard",
        text="\n\n".join(
            [
                format_task_list(today_tasks, title="📅 Задачи на сегодня", limit=DEFAULT_TASK_LIMIT),
                format_task_list(overdue_tasks, title="⏰ Просроченные задачи", limit=DEFAULT_TASK_LIMIT),
                format_contacts_list(today_contacts, title="📞 Контакты на сегодня", limit=DEFAULT_TASK_LIMIT),
                format_contacts_list(overdue_contacts, title="🚨 Просроченные контакты", limit=DEFAULT_TASK_LIMIT),
            ]
        ),
        reply_markup=get_tasks_menu_keyboard(),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.message(F.text == TODAY_TASKS_TEXT)
async def show_today_tasks(message: Message, state: FSMContext, auth_service: AuthService, task_service: TaskService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    tasks = list(await task_service.get_today_tasks(current_user=user, limit=DEFAULT_TASK_LIMIT))
    await send_clean_screen(
        message,
        state=state,
        scope="tasks_list",
        text=format_task_list(tasks, title="📅 Задачи на сегодня", limit=DEFAULT_TASK_LIMIT),
        reply_markup=get_task_list_inline_keyboard(tasks),
        prefer_edit=False,
    )


@router.message(F.text == OVERDUE_TASKS_TEXT)
async def show_overdue_tasks(message: Message, state: FSMContext, auth_service: AuthService, task_service: TaskService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    tasks = list(await task_service.get_overdue_tasks(current_user=user, limit=DEFAULT_TASK_LIMIT))
    await send_clean_screen(
        message,
        state=state,
        scope="tasks_list",
        text=format_task_list(tasks, title="⏰ Просроченные задачи", limit=DEFAULT_TASK_LIMIT),
        reply_markup=get_task_list_inline_keyboard(tasks),
        prefer_edit=False,
    )


@router.message(F.text == TODAY_CONTACTS_TEXT)
async def show_today_contacts(message: Message, state: FSMContext, auth_service: AuthService, client_service: ClientService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    clients = list(await client_service.get_today_contacts(current_user=user, limit=DEFAULT_TASK_LIMIT))
    await send_clean_screen(message, state=state, scope="contacts_list", text=format_contacts_list(clients, title="📞 Контакты на сегодня", limit=DEFAULT_TASK_LIMIT), parse_mode="HTML", prefer_edit=False)


@router.message(F.text == OVERDUE_CONTACTS_TEXT)
async def show_overdue_contacts(message: Message, state: FSMContext, auth_service: AuthService, client_service: ClientService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    clients = list(await client_service.get_overdue_contacts(current_user=user, limit=DEFAULT_TASK_LIMIT))
    await send_clean_screen(message, state=state, scope="contacts_list", text=format_contacts_list(clients, title="🚨 Просроченные контакты", limit=DEFAULT_TASK_LIMIT), parse_mode="HTML", prefer_edit=False)


@router.message(F.text == MY_TASKS_TEXT)
async def show_my_tasks(message: Message, state: FSMContext, auth_service: AuthService, task_service: TaskService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    tasks = list(await task_service.get_my_tasks(current_user=user, limit=DEFAULT_TASK_LIMIT))
    await send_clean_screen(
        message,
        state=state,
        scope="tasks_list",
        text=format_task_list(tasks, title="🗂 Мои задачи", limit=DEFAULT_TASK_LIMIT),
        reply_markup=get_task_list_inline_keyboard(tasks),
        prefer_edit=False,
    )


@router.callback_query(F.data == "tasks_all")
async def show_all_tasks_from_callback(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    task_service: TaskService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    tasks = list(await task_service.get_my_tasks(current_user=user, limit=DEFAULT_TASK_LIMIT))
    await send_clean_screen(
        callback,
        state=state,
        scope="tasks_list",
        text=format_task_list(tasks, title="🗂 Все задачи", limit=DEFAULT_TASK_LIMIT),
        reply_markup=get_task_list_inline_keyboard(tasks),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task_open:"))
async def show_task_card(callback: CallbackQuery, state: FSMContext, auth_service: AuthService, task_service: TaskService) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    task_id_raw = callback.data.split(":", maxsplit=1)[1]
    if not task_id_raw.isdigit():
        await callback.answer("Некорректный ID задачи", show_alert=True)
        return
    task = await task_service.get_task_by_id(current_user=user, task_id=int(task_id_raw))
    if task is None:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    await send_clean_screen(
        callback,
        state=state,
        scope="task_card",
        text=format_task_card(task),
        reply_markup=get_task_card_actions_keyboard(task),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("contact_task_card:"))
async def show_contact_task_card(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    task_service: TaskService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    client_id_raw = callback.data.split(":", maxsplit=1)[1]
    if not client_id_raw.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    task = await task_service.get_nearest_client_task(current_user=user, client_id=int(client_id_raw))
    if task is None:
        await callback.answer("У этого клиента нет активной задачи", show_alert=True)
        return

    await send_clean_screen(
        callback,
        state=state,
        scope="task_card",
        text=format_task_card(task),
        reply_markup=get_task_card_actions_keyboard(task),
        parse_mode="HTML",
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task_complete:"))
async def complete_task_from_callback(
    callback: CallbackQuery,
    auth_service: AuthService,
    task_service: TaskService,
    session: AsyncSession,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    task_id_raw = callback.data.split(":", maxsplit=1)[1]
    if not task_id_raw.isdigit():
        await callback.answer("Некорректный ID задачи", show_alert=True)
        return

    task = await task_service.complete_task(current_user=user, task_id=int(task_id_raw))
    if task is None:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    await session.commit()
    with suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=get_task_reminder_keyboard(task, completed=True))
    await callback.answer("Задача завершена")


@router.callback_query(F.data.startswith("contact_done:"))
async def complete_contact_from_callback(
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

    client_id_raw = callback.data.split(":", maxsplit=1)[1]
    if not client_id_raw.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    client = await client_service.get_client_for_view(current_user=user, client_id=int(client_id_raw))
    if client is None:
        await callback.answer("Клиент не найден или нет прав на просмотр", show_alert=True)
        return

    try:
        if client.next_contact_at is not None:
            client = await client_service.update_next_contact(
                current_user=user,
                client_id=client.id,
                next_contact_at=None,
            )
            await session.commit()
    except PermissionError as error:
        await callback.answer(str(error), show_alert=True)
        return
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    with suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=get_contact_reminder_keyboard(client, completed=True))
    await callback.answer("Контакт завершён")
