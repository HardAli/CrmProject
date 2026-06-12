from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.supervisor import (
    ADMIN_PASS_BUTTON_TEXT,
    EXIT_TO_MENU_BUTTON_TEXT,
    MANAGER_PASS_BUTTON_TEXT,
    SUPERVISOR_MENU_COMMAND,
    USERS_BUTTON_TEXT,
    get_supervisor_menu_keyboard,
)
from app.bot.utils.chat_ui import send_clean_screen
from app.common.enums import UserRole
from app.common.formatters.role_formatter import (
    format_pass_error,
    format_role_applied,
    format_role_pass,
    format_users_list,
)
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.role_pass_service import RolePassService
from app.services.role_service import RoleService

router = Router(name="roles")


async def _get_current_user(message: Message, auth_service: AuthService):
    if message.from_user is None:
        return None
    return await auth_service.get_active_user_by_telegram_id(message.from_user.id)


@router.message(Command(SUPERVISOR_MENU_COMMAND.lstrip("/")))
async def open_supervisor_panel(message: Message, state: FSMContext, auth_service: AuthService, role_service: RoleService) -> None:
    user = await _get_current_user(message, auth_service)
    if not role_service.can_open_supervisor_panel(user):
        await message.answer("Доступ запрещён.")
        return

    await send_clean_screen(message, state=state, scope="supervisor_menu", text="Панель supervisor", reply_markup=get_supervisor_menu_keyboard(), prefer_edit=False)


@router.message(F.text == USERS_BUTTON_TEXT)
async def show_users(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    role_service: RoleService,
    user_repository: UserRepository,
) -> None:
    user = await _get_current_user(message, auth_service)
    if not role_service.can_open_supervisor_panel(user):
        await message.answer("Доступ запрещён.")
        return

    users = await user_repository.list_users(limit=50, offset=0)
    await send_clean_screen(message, state=state, scope="supervisor_users", text=format_users_list(users, limit=50), prefer_edit=False)


@router.message(F.text == MANAGER_PASS_BUTTON_TEXT)
async def generate_manager_pass(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    role_service: RoleService,
    role_pass_service: RolePassService,
    session: AsyncSession,
) -> None:
    user = await _get_current_user(message, auth_service)
    if not role_service.can_open_supervisor_panel(user):
        await message.answer("Доступ запрещён.")
        return

    role_pass = await role_pass_service.generate_manager_pass(user)
    await session.commit()
    await send_clean_screen(message, state=state, scope="supervisor_role_pass", text=format_role_pass(role_pass), parse_mode="HTML", prefer_edit=False)


@router.message(F.text == ADMIN_PASS_BUTTON_TEXT)
async def generate_admin_pass(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    role_service: RoleService,
    role_pass_service: RolePassService,
    session: AsyncSession,
) -> None:
    user = await _get_current_user(message, auth_service)
    if not role_service.can_open_supervisor_panel(user):
        await message.answer("Доступ запрещён.")
        return

    role_pass = await role_pass_service.generate_admin_pass(user)
    await session.commit()
    await send_clean_screen(message, state=state, scope="supervisor_role_pass", text=format_role_pass(role_pass), parse_mode="HTML", prefer_edit=False)


@router.message(F.text == EXIT_TO_MENU_BUTTON_TEXT)
async def exit_supervisor_menu(message: Message, state: FSMContext) -> None:
    await send_clean_screen(message, state=state, scope="main_menu", text="Возврат в главное меню.", reply_markup=get_main_menu_keyboard(), prefer_edit=False)


@router.message(F.text)
async def process_role_text(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    role_service: RoleService,
    user_repository: UserRepository,
    session: AsyncSession,
) -> None:
    if message.from_user is None or not message.text or message.text.startswith("/"):
        return

    promoted = await role_service.promote_to_supervisor_by_secret(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        message_text=message.text,
    )
    if promoted is not None:
        await session.commit()
        await send_clean_screen(message, state=state, scope="role_applied", text="Роль supervisor успешно выдана.", prefer_edit=False)
        return

    if re.fullmatch(r"[A-Z0-9]{10}", message.text) is None:
        return

    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        user = await user_repository.get_or_create_by_telegram_user(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            default_role=UserRole.MANAGER,
        )

    result = await role_service.apply_role_passcode(user=user, code=message.text)
    if not result.success:
        await send_clean_screen(message, state=state, scope="role_pass_error", text=format_pass_error(result.reason), prefer_edit=False)
        return

    await session.commit()
    await send_clean_screen(message, state=state, scope="role_applied", text=format_role_applied(result.role.value if result.role else "manager"), prefer_edit=False)
