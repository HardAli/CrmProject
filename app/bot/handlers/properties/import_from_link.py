from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.properties.create import _parse_positive_int, _parse_rooms
from app.bot.keyboards.clients import CANCEL_TEXT
from app.bot.keyboards.properties import (
    PROPERTY_STATUS_MAP,
    PROPERTY_TYPE_MAP,
    get_properties_menu_keyboard,
    get_property_district_keyboard,
    get_property_rooms_keyboard,
    get_property_status_keyboard,
    get_property_type_keyboard,
)
from app.bot.keyboards.properties_import import (
    ADD_PROPERTY_BY_LINK_TEXT,
    FILL_MISSING_FIELDS_TEXT,
    SAVE_IMPORTED_PROPERTY_TEXT,
    get_property_import_preview_keyboard,
    get_property_import_url_keyboard,
)
from app.bot.states.property_import_states import PropertyImportStates
from app.common.enums import PropertyStatus, PropertyType
from app.common.formatters.property_formatter import format_property_created_card
from app.common.formatters.property_import_formatter import format_import_success
from app.common.utils.parsers import parse_money
from app.common.utils.phone_links import normalize_owner_phone
from app.common.utils.value_parsers import parse_decimal_or_none, parse_int_or_none
from app.services.auth_service import AuthService
from app.services.property_import_service import InvalidListingUrlError, PropertyImportService

router = Router(name="property_import")


async def _get_user(message: Message, auth_service: AuthService):
    if message.from_user is None:
        return None
    return await auth_service.get_active_user_by_telegram_id(message.from_user.id)


@router.message(F.text == ADD_PROPERTY_BY_LINK_TEXT)
async def start_import(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    user = await _get_user(message, auth_service)
    if user is None:
        await message.answer("У вас нет доступа к этой функции.")
        return
    await state.clear()
    await state.set_state(PropertyImportStates.waiting_for_url)
    await message.answer("Отправьте ссылку на объявление (пока поддерживается Krisha.kz).", reply_markup=get_property_import_url_keyboard())


@router.message(StateFilter(PropertyImportStates.waiting_for_url), F.text == CANCEL_TEXT)
@router.message(StateFilter(PropertyImportStates.preview), F.text == CANCEL_TEXT)
@router.message(StateFilter(PropertyImportStates.fill_missing), F.text == CANCEL_TEXT)
async def cancel_import(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Импорт по ссылке отменён.", reply_markup=get_properties_menu_keyboard())


@router.message(PropertyImportStates.waiting_for_url)
async def parse_url(
    message: Message,
    state: FSMContext,
    property_import_service: PropertyImportService,
) -> None:
    try:
        url = property_import_service.validate_url(message.text or "")
    except InvalidListingUrlError as error:
        await message.answer(str(error), parse_mode=None)
        return

    raw_data = await property_import_service.parse_listing(url)
    parsed = property_import_service.normalize_parsed_data(raw_data)
    preview = property_import_service.build_preview(parsed)
    payload = property_import_service.to_state_payload(parsed)
    await state.update_data(import_payload=payload)
    await state.set_state(PropertyImportStates.preview)
    await message.answer(
        preview,
        reply_markup=get_property_import_preview_keyboard(has_missing_fields=not parsed.is_complete_for_create),
        parse_mode=None,
    )


def _read_payload(state_data: dict[str, object]) -> dict[str, object]:
    payload = state_data.get("import_payload")
    return payload if isinstance(payload, dict) else {}


def _compute_missing(payload: dict[str, object]) -> list[str]:
    required = ["title", "property_type", "district", "address", "owner_phone", "price", "area", "rooms", "floor", "status"]
    missing = [field for field in required if payload.get(field) in (None, "")]
    if payload.get("property_type") == PropertyType.APARTMENT.value and payload.get("building_floors") in (None, ""):
        missing.append("building_floors")
    return missing


async def _ask_next_missing(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    payload = _read_payload(data)
    missing = _compute_missing(payload)
    if not missing:
        await state.set_state(PropertyImportStates.preview)
        await message.answer("Все обязательные поля заполнены. Нажмите «Сохранить».", reply_markup=get_property_import_preview_keyboard(has_missing_fields=False))
        return False

    field = missing[0]
    await state.update_data(current_missing_field=field)
    if field == "property_type":
        await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())
    elif field == "district":
        await message.answer("Выберите район кнопкой или введите вручную.", reply_markup=get_property_district_keyboard())
    elif field == "rooms":
        await message.answer("Выберите комнаты:", reply_markup=get_property_rooms_keyboard())
    elif field == "status":
        await message.answer("Выберите статус:", reply_markup=get_property_status_keyboard())
    else:
        await message.answer(f"Введите значение для поля: {field}")
    await state.set_state(PropertyImportStates.fill_missing)
    return True


@router.message(PropertyImportStates.preview, F.text == FILL_MISSING_FIELDS_TEXT)
async def fill_missing(message: Message, state: FSMContext) -> None:
    await _ask_next_missing(message, state)


@router.message(PropertyImportStates.fill_missing)
async def process_missing(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    payload = _read_payload(data)
    field = data.get("current_missing_field")

    text = (message.text or "").strip()
    if field == "property_type":
        enum_value = PROPERTY_TYPE_MAP.get(text)
        if enum_value is None:
            await message.answer("Выберите тип кнопкой.", reply_markup=get_property_type_keyboard())
            return
        payload[field] = enum_value.value
    elif field == "status":
        status = PROPERTY_STATUS_MAP.get(text)
        if status is None:
            await message.answer("Выберите статус кнопкой.", reply_markup=get_property_status_keyboard())
            return
        payload[field] = status.value
    elif field == "price" or field == "area":
        payload[field] = str(parse_money(text))
    elif field == "owner_phone":
        payload[field] = normalize_owner_phone(text)
    elif field == "rooms":
        payload[field] = _parse_rooms(text)
    elif field == "floor" or field == "building_floors":
        payload[field] = _parse_positive_int(text, field)
    else:
        payload[field] = text

    await state.update_data(import_payload=payload)
    has_next = await _ask_next_missing(message, state)
    if not has_next:
        await state.set_state(PropertyImportStates.preview)


@router.message(PropertyImportStates.preview, F.text == SAVE_IMPORTED_PROPERTY_TEXT)
async def save_import(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    property_import_service: PropertyImportService,
    session: AsyncSession,
) -> None:
    user = await _get_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    data = await state.get_data()
    payload = _read_payload(data)
    missing = _compute_missing(payload)
    if missing:
        await message.answer("Есть незаполненные обязательные поля. Нажмите «Заполнить недостающие поля».", reply_markup=get_property_import_preview_keyboard(has_missing_fields=True))
        return

    from app.schemas.parsed_property import ParsedPropertyData

    parsed = ParsedPropertyData(
        source=str(payload.get("source", "krisha")),
        source_url=str(payload.get("source_url", "")),
        source_listing_id=payload.get("source_listing_id"),
        title=str(payload.get("title")),
        property_type=PropertyType(str(payload.get("property_type"))),
        district=str(payload.get("district")),
        address=str(payload.get("address")),
        owner_phone=str(payload.get("owner_phone")),
        owner_phone_normalized=str(payload.get("owner_phone_normalized")) if payload.get("owner_phone_normalized") else None,
        price=parse_decimal_or_none(payload.get("price")) or Decimal(0),
        area=parse_decimal_or_none(payload.get("area")) or Decimal(0),
        rooms=parse_int_or_none(payload.get("rooms")),
        floor=parse_int_or_none(payload.get("floor")),
        building_floors=parse_int_or_none(payload.get("building_floors")),
        description=str(payload.get("description")) if payload.get("description") else None,
        status=PropertyStatus(str(payload.get("status", PropertyStatus.ACTIVE.value))),
        image_urls=payload.get("image_urls", []),
        parse_warnings=payload.get("parse_warnings", []),
    )

    property_obj, linked_clients_count, photo_count = await property_import_service.create_property_from_parsed_data(
        current_user=user,
        parsed_data=parsed,
    )
    await session.commit()
    await state.clear()

    manager_name = property_obj.manager.full_name if property_obj.manager else user.full_name
    await message.answer(format_import_success(property_id=property_obj.id, linked_clients_count=linked_clients_count, photo_count=photo_count))
    await message.answer(format_property_created_card(property_obj=property_obj, manager_name=manager_name),
                         reply_markup=get_properties_menu_keyboard())
