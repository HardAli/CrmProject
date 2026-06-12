from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.supervisor import SUPERVISOR_MENU_COMMAND, get_supervisor_menu_keyboard
from app.bot.utils.chat_ui import send_clean_screen
from app.services.auth_service import AuthService
from app.services.role_service import RoleService

router = Router(name="start")


async def _render_main_menu(target: Message | CallbackQuery, state: FSMContext, text: str) -> None:
    await state.clear()
    await send_clean_screen(
        target,
        state=state,
        scope="main_menu",
        text=text,
        reply_markup=get_main_menu_keyboard(),
        prefer_edit=isinstance(target, CallbackQuery),
    )


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        await message.answer("Не удалось определить ваш профиль Telegram. Попробуйте снова.")
        return

    user = await auth_service.get_active_user_by_telegram_id(telegram_user.id)

    if user is None:
        await message.answer("У вас нет доступа")
        return

    await _render_main_menu(
        message,
        state=state,
        text=(
            f"Здравствуйте, {user.full_name}!\n"
            "Добро пожаловать в CRM-бот агентства недвижимости."
        ),
    )


@router.callback_query(F.data == "main_menu_open")
async def open_main_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await _render_main_menu(callback, state=state, text="Главное меню:")
    await callback.answer()


@router.message(Command(SUPERVISOR_MENU_COMMAND.lstrip("/")))
async def supervisor_command(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    role_service: RoleService,
) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        await message.answer("Не удалось определить ваш профиль Telegram. Попробуйте снова.")
        return

    user = await auth_service.get_active_user_by_telegram_id(telegram_user.id)
    if not role_service.can_open_supervisor_panel(user):
        await message.answer("Доступ запрещён.")
        return

    await state.clear()
    await send_clean_screen(
        message,
        state=state,
        scope="supervisor_menu",
        text="Панель supervisor",
        reply_markup=get_supervisor_menu_keyboard(),
        prefer_edit=False,
    )
