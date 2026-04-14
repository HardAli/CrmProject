from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.services.auth_service import AuthService

router = Router(name="start")


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