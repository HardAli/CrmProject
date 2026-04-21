from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import (
    CANCEL_TEXT,
    get_cancel_keyboard,
    get_client_photo_delete_keyboard,
    get_client_photos_menu_keyboard,
)
from app.bot.states.clients import ClientCardStates
from app.services.auth_service import AuthService
from app.services.client_photo_service import ClientPhotoService

router = Router(name="client_photos")
DEFAULT_PHOTOS_LIMIT = 20


@router.callback_query(F.data.startswith("client_photos:"))
async def open_client_photos_menu(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_photo_service: ClientPhotoService,
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

    client_id = int(raw_client_id)
    try:
        can_manage = await client_photo_service.can_manage_client_photos_for_client(
            current_user=user,
            client_id=client_id,
        )
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return

    await callback.message.answer(
        "Раздел фото клиента. Выберите действие:",
        reply_markup=get_client_photos_menu_keyboard(client_id=client_id, can_manage=can_manage),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_photo_add:"))
async def start_add_photo(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    client_photo_service: ClientPhotoService,
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

    client_id = int(raw_client_id)
    try:
        can_manage = await client_photo_service.can_manage_client_photos_for_client(
            current_user=user,
            client_id=client_id,
        )
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return
    if not can_manage:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await state.set_state(ClientCardStates.add_photo)
    await state.update_data(client_id=client_id)

    await callback.message.answer(
        "Отправьте одну фотографию клиента одним сообщением. Подпись к фото будет сохранена автоматически.",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(Command("cancel"), ClientCardStates.add_photo)
@router.message(F.text == CANCEL_TEXT, ClientCardStates.add_photo)
async def cancel_add_photo(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добавление фото отменено.")


@router.message(ClientCardStates.add_photo)
async def save_client_photo(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    client_photo_service: ClientPhotoService,
    session: AsyncSession,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя Telegram.")
        return

    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer("Нет доступа")
        return

    if not message.photo:
        await message.answer("Нужно отправить именно фотографию. Попробуйте ещё раз или нажмите «Отмена».")
        return

    state_data = await state.get_data()
    client_id = state_data.get("client_id")
    if not isinstance(client_id, int):
        await state.clear()
        await message.answer("Не удалось определить клиента. Откройте карточку заново.")
        return

    file_id = message.photo[-1].file_id
    caption = message.caption

    try:
        photo = await client_photo_service.add_client_photo(
            current_user=user,
            client_id=client_id,
            telegram_file_id=file_id,
            caption=caption,
        )
    except ValueError:
        await state.clear()
        await message.answer("Клиент не найден или недоступен.")
        return
    except PermissionError:
        await state.clear()
        await message.answer("У вас нет прав на добавление фото.")
        return

    await session.commit()
    await state.clear()

    await message.answer(
        f"Фото сохранено ✅\nID фото: {photo.id}",
        reply_markup=get_client_photos_menu_keyboard(client_id=client_id, can_manage=True),
    )


@router.callback_query(F.data.startswith("client_photo_view:"))
async def view_client_photos(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_photo_service: ClientPhotoService,
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

    client_id = int(raw_client_id)
    try:
        photos = list(
            await client_photo_service.get_client_photos(
                current_user=user,
                client_id=client_id,
                limit=DEFAULT_PHOTOS_LIMIT,
            )
        )
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return

    if not photos:
        await callback.message.answer("У этого клиента пока нет фотографий.")
        await callback.answer()
        return

    for index, photo in enumerate(photos, start=1):
        caption = photo.caption or f"Фото #{index} (ID: {photo.id})"
        await callback.message.answer_photo(photo.telegram_file_id, caption=caption)

    await callback.answer()


@router.callback_query(F.data.startswith("client_photo_delete_menu:"))
async def delete_client_photo_menu(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_photo_service: ClientPhotoService,
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

    client_id = int(raw_client_id)
    try:
        photos = list(await client_photo_service.get_client_photos(current_user=user, client_id=client_id))
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return

    if not photos:
        await callback.answer("Нет фото для удаления", show_alert=True)
        return

    if not client_photo_service.can_manage_client_photos(current_user=user, client=photos[0].client):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    delete_items = [(photo.id, f"🗑 Фото #{photo.id}") for photo in photos]
    await callback.message.answer(
        "Выберите фотографию для удаления:",
        reply_markup=get_client_photo_delete_keyboard(client_id=client_id, photos=delete_items),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_photo_delete:"))
async def delete_client_photo(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_photo_service: ClientPhotoService,
    session: AsyncSession,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_client_id, raw_photo_id = callback.data.split(":", maxsplit=2)
    if not raw_client_id.isdigit() or not raw_photo_id.isdigit():
        await callback.answer("Некорректные идентификаторы", show_alert=True)
        return

    client_id = int(raw_client_id)
    photo_id = int(raw_photo_id)

    try:
        await client_photo_service.delete_client_photo(current_user=user, photo_id=photo_id)
    except ValueError:
        await callback.answer("Фото не найдено", show_alert=True)
        return
    except PermissionError:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await session.commit()
    await callback.message.answer(
        "Фото удалено ✅",
        reply_markup=get_client_photos_menu_keyboard(client_id=client_id, can_manage=True),
    )
    await callback.answer()