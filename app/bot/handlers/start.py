from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserRole
from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = Router(name="start")


@router.message(F.text == "HardAdmin123")
async def grant_admin_role(
    message: Message,
    user_repository: UserRepository,
    session: AsyncSession,
) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        await message.answer("Не удалось определить ваш профиль Telegram. Попробуйте снова.")
        return

    user = await user_repository.get_by_telegram_id(telegram_user.id)
    if user is None:
        await user_repository.create(
            telegram_id=telegram_user.id,
            full_name=telegram_user.full_name,
            role=UserRole.ADMIN,
        )
    else:
        await user_repository.set_role(user, UserRole.ADMIN)
        user.is_active = True
    await session.commit()
    await message.answer("Вам выданы права администратора.")


@router.message(CommandStart())
async def start_command(message: Message, auth_service: AuthService) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        await message.answer("Не удалось определить ваш профиль Telegram. Попробуйте снова.")
        return

    user = await auth_service.get_active_user_by_telegram_id(telegram_user.id)

    if user is None:
        await message.answer("У вас нет доступа")
        return

    await message.answer(
        text=(
            f"Здравствуйте, {user.full_name}!\n"
            "Добро пожаловать в CRM-бот агентства недвижимости."
        ),
        reply_markup=get_main_menu_keyboard(),
    )