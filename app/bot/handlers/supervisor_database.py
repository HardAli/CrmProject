from __future__ import annotations

import logging
from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.supervisor import EXIT_TO_MENU_BUTTON_TEXT, get_supervisor_menu_keyboard
from app.bot.keyboards.supervisor_database import (
    DATABASE_BACK_BUTTON_TEXT,
    DATABASE_BUTTON_TEXT,
    DATABASE_EXPORT_BUTTON_TEXT,
    DATABASE_IMPORT_BUTTON_TEXT,
    get_supervisor_database_keyboard,
)
from app.bot.states.database_import_states import DatabaseImportStates
from app.common.formatters.database_export_formatter import format_database_export_summary
from app.common.formatters.database_import_formatter import format_database_import_report
from app.services.auth_service import AuthService
from app.services.database_export_service import DatabaseExportService
from app.services.database_import_service import DatabaseImportService, InvalidDatabaseArchiveError
from app.services.role_service import RoleService

logger = logging.getLogger(__name__)
router = Router(name="supervisor_database")


async def _is_supervisor(message: Message, auth_service: AuthService, role_service: RoleService) -> bool:
    if message.from_user is None:
        return False
    current_user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    return role_service.can_open_supervisor_panel(current_user)


@router.message(F.text == DATABASE_BUTTON_TEXT)
async def open_database_menu(
    message: Message,
    auth_service: AuthService,
    role_service: RoleService,
    state: FSMContext,
) -> None:
    if not await _is_supervisor(message, auth_service, role_service):
        await message.answer("Доступ запрещён.")
        return

    await state.clear()
    await message.answer("Меню базы данных", reply_markup=get_supervisor_database_keyboard())


@router.message(F.text == DATABASE_BACK_BUTTON_TEXT)
async def back_to_supervisor_menu(
    message: Message,
    auth_service: AuthService,
    role_service: RoleService,
    state: FSMContext,
) -> None:
    if not await _is_supervisor(message, auth_service, role_service):
        await message.answer("Доступ запрещён.")
        return

    await state.clear()
    await message.answer("Панель supervisor", reply_markup=get_supervisor_menu_keyboard())


@router.message(F.text == DATABASE_EXPORT_BUTTON_TEXT)
async def export_database(
    message: Message,
    auth_service: AuthService,
    role_service: RoleService,
    database_export_service: DatabaseExportService,
) -> None:
    if not await _is_supervisor(message, auth_service, role_service):
        await message.answer("Доступ запрещён.")
        return

    try:
        export_result = await database_export_service.export()
    except Exception:
        logger.exception("Database export failed")
        await message.answer("Не удалось сформировать экспорт базы. Подробности записаны в лог.")
        return

    await message.answer_document(
        BufferedInputFile(export_result.payload, filename=export_result.file_name),
        caption="Архив экспорта базы данных.",
    )
    await message.answer(format_database_export_summary(export_result))


@router.message(F.text == DATABASE_IMPORT_BUTTON_TEXT)
async def request_import_archive(
    message: Message,
    auth_service: AuthService,
    role_service: RoleService,
    state: FSMContext,
) -> None:
    if not await _is_supervisor(message, auth_service, role_service):
        await message.answer("Доступ запрещён.")
        return

    await state.set_state(DatabaseImportStates.waiting_for_archive)
    await message.answer("Отправьте zip-файл экспорта базы данных (формат crm.entities.zip).")


@router.message(DatabaseImportStates.waiting_for_archive, F.document)
async def import_database_archive(
    message: Message,
    auth_service: AuthService,
    role_service: RoleService,
    database_import_service: DatabaseImportService,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if not await _is_supervisor(message, auth_service, role_service):
        await message.answer("Доступ запрещён.")
        await state.clear()
        return

    document = message.document
    if document is None:
        await message.answer("Не удалось прочитать документ. Отправьте файл заново.")
        return

    file = await message.bot.get_file(document.file_id)
    stream = BytesIO()
    await message.bot.download_file(file.file_path, destination=stream)
    payload = stream.getvalue()

    try:
        report = await database_import_service.import_archive(payload)
        await session.commit()
    except InvalidDatabaseArchiveError as exc:
        await session.rollback()
        await message.answer(f"Файл не подходит для импорта: {exc}")
        return
    except Exception:
        await session.rollback()
        logger.exception("Database import failed")
        await message.answer("Импорт завершился ошибкой. Подробности записаны в лог.")
        return
    finally:
        await state.clear()

    await message.answer(format_database_import_report(report))


@router.message(DatabaseImportStates.waiting_for_archive)
async def import_waiting_for_document(
    message: Message,
    auth_service: AuthService,
    role_service: RoleService,
) -> None:
    if not await _is_supervisor(message, auth_service, role_service):
        await message.answer("Доступ запрещён.")
        return

    if message.text == EXIT_TO_MENU_BUTTON_TEXT:
        await message.answer("Возврат в главное меню.", reply_markup=get_main_menu_keyboard())
        return

    await message.answer("Ожидаю zip-файл экспорта. Отправьте документом.")