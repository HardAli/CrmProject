from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import (
    CANCEL_TEXT,
    DONE_TEXT,
    get_client_photo_delete_keyboard,
    get_client_photo_upload_keyboard,
    get_client_photos_menu_keyboard,
)
from app.bot.handlers.clients.photo_media_group import buffer_media_group_photo
from app.database.session import session_scope
from app.repositories.client_photo_repository import ClientPhotoRepository
from app.repositories.clients import ClientRepository
from app.repositories.user_repository import UserRepository
from app.bot.states.clients import ClientCardStates
from app.services.auth_service import AuthService
from app.services.client_photo_service import ClientPhotoService

router = Router(name="client_photos")
logger = logging.getLogger(__name__)


def _is_missing_photo_unique_id_column(error: ProgrammingError) -> bool:
    error_text = str(getattr(error, "orig", error)).lower()
    return (
        "client_photos.telegram_file_unique_id" in error_text
        and "does not exist" in error_text
    )


async def _save_photos_with_new_session(
    *,
    telegram_user_id: int,
    client_id: int,
    photos: list[tuple[str, str | None]],
) -> tuple[int, int]:
    async with session_scope() as session:
        user_repository = UserRepository(session)
        auth_service = AuthService(user_repository=user_repository)
        current_user = await auth_service.get_active_user_by_telegram_id(telegram_user_id)
        if current_user is None:
            return 0, 0

        client_photo_service = ClientPhotoService(
            client_photo_repository=ClientPhotoRepository(session=session),
            client_repository=ClientRepository(session=session),
        )
        saved_count, duplicate_count = await client_photo_service.add_client_photos_bulk(
            current_user=current_user,
            client_id=client_id,
            photos=photos,
        )
        await session.commit()
        return saved_count, duplicate_count


async def _process_media_group_batch(
    *,
    message: Message,
    telegram_user_id: int,
    client_id: int,
    photos: list[tuple[str, str | None]],
) -> None:
    try:
        saved_count, duplicate_count = await _save_photos_with_new_session(
            telegram_user_id=telegram_user_id,
            client_id=client_id,
            photos=photos,
        )
    except (PermissionError, ValueError):
        await message.answer("Клиент не найден.")
        return
    except Exception:
        await message.answer("Не удалось сохранить фотографии. Попробуйте позже.")
        return

    if duplicate_count:
        await message.answer(
            f"Сохранено фото: {saved_count}. Дубликатов пропущено: {duplicate_count}."
        )
        return
    await message.answer(f"Сохранено фото: {saved_count}.")


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
        photos_count = await client_photo_service.count_client_photos(current_user=user, client_id=client_id)
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return
    except ProgrammingError as error:
        if _is_missing_photo_unique_id_column(error):
            logger.exception(
                "Database schema is out of sync: missing client_photos.telegram_file_unique_id. "
                "Run alembic upgrade head."
            )
            await callback.answer("База данных не синхронизирована. Обратитесь к администратору.", show_alert=True)
            return
        raise

    await callback.message.answer(
        f"Раздел фото клиента.\nКоличество фото: {photos_count}.\nВыберите действие:",
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
        "Отправьте одну или несколько фотографий клиента. Можно отправить альбомом до 10 фото. "
        "Когда закончите, нажмите «Готово».",
        reply_markup=get_client_photo_upload_keyboard(),
    )
    await callback.answer()


@router.message(Command("cancel"), ClientCardStates.add_photo)
@router.message(F.text == CANCEL_TEXT, ClientCardStates.add_photo)
async def cancel_add_photo(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добавление фото отменено.")


@router.message(Command("done"), ClientCardStates.add_photo)
@router.message(F.text == DONE_TEXT, ClientCardStates.add_photo)
async def finish_add_photo(message: Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    client_id = state_data.get("client_id")
    await state.clear()

    if isinstance(client_id, int):
        await message.answer(
            "Загрузка фото завершена.",
            reply_markup=get_client_photos_menu_keyboard(client_id=client_id, can_manage=True),
        )
        return

    await message.answer("Загрузка фото завершена.")


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
        await message.answer(
            "Пожалуйста, отправьте фото клиента. "
            "Можно отправить сразу несколько фотографий альбомом."
        )
        return

    state_data = await state.get_data()
    client_id = state_data.get("client_id")
    if not isinstance(client_id, int):
        await state.clear()
        await message.answer("Не удалось определить клиента. Откройте карточку заново.")
        return

    try:
        can_manage = await client_photo_service.can_manage_client_photos_for_client(
            current_user=user,
            client_id=client_id,
        )
    except ValueError:
        await state.clear()
        await message.answer("Клиент не найден.")
        return
    if not can_manage:
        await state.clear()
        await message.answer("У вас нет прав на добавление фото.")
        return

    photo = message.photo[-1]
    file_id = photo.file_id
    file_unique_id = photo.file_unique_id

    if message.media_group_id:
        key = f"client_photo:{client_id}:{message.from_user.id}:{message.media_group_id}"
        await buffer_media_group_photo(
            key=key,
            photo=(file_id, file_unique_id),
            on_ready=lambda photos: _process_media_group_batch(
                message=message,
                telegram_user_id=message.from_user.id,
                client_id=client_id,
                photos=photos,
            ),
        )
        return

    try:
        saved_photo = await client_photo_service.add_client_photo(
            current_user=user,
            client_id=client_id,
            telegram_file_id=file_id,
            telegram_file_unique_id=file_unique_id,
        )
    except (ValueError, PermissionError):
        await state.clear()
        await message.answer("Клиент не найден.")
        return

    await session.commit()

    if saved_photo is None:
        await message.answer(
            "Сохранено фото: 0. Дубликатов пропущено: 1.",
            reply_markup=get_client_photo_upload_keyboard(),
        )
        return

    await message.answer("Фото сохранено.", reply_markup=get_client_photo_upload_keyboard())


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
            )
        )
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return
    except ProgrammingError as error:
        if _is_missing_photo_unique_id_column(error):
            logger.exception(
                "Database schema is out of sync: missing client_photos.telegram_file_unique_id. "
                "Run alembic upgrade head."
            )
            await callback.answer("База данных не синхронизирована. Обратитесь к администратору.", show_alert=True)
            return
        raise

    if not photos:
        await callback.message.answer("У клиента пока нет фотографий.")
        await callback.answer()
        return

    await callback.message.answer(f"Количество фото клиента: {len(photos)}.")
    for offset in range(0, len(photos), 10):
        chunk = photos[offset:offset + 10]
        media = [InputMediaPhoto(media=photo.telegram_file_id) for photo in chunk]
        await callback.message.answer_media_group(media=media)

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
    except ProgrammingError as error:
        if _is_missing_photo_unique_id_column(error):
            logger.exception(
                "Database schema is out of sync: missing client_photos.telegram_file_unique_id. "
                "Run alembic upgrade head."
            )
            await callback.answer("База данных не синхронизирована. Обратитесь к администратору.", show_alert=True)
            return
        raise

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
