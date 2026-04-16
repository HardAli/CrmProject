from __future__ import annotations

from decimal import Decimal
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import CANCEL_TEXT, SKIP_TEXT
from app.bot.keyboards.properties import (
    ADD_PROPERTY_TEXT,
    PROPERTY_STATUS_MAP,
    PROPERTY_TYPE_MAP,
    get_properties_menu_keyboard,
    get_property_cancel_keyboard,
    get_property_skip_cancel_keyboard,
    get_property_status_keyboard,
    get_property_type_keyboard,
)
from app.bot.states.properties import PropertyCreateStates
from app.common.dto.properties import CreatePropertyDTO
from app.common.enums import PropertyStatus, PropertyType
from app.common.formatters.property_formatter import format_property_created_card
from app.common.utils.parsers import parse_money
from app.common.utils.phone_links import normalize_owner_phone
from app.services.auth_service import AuthService
from app.services.properties import PropertyService

router = Router(name="property_create")


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


def _parse_positive_int_or_skip(raw_value: str, field_name: str) -> int | None:
    value = raw_value.strip()
    if value == SKIP_TEXT or value in {"-", "—"}:
        return None
    if value.isdigit() and int(value) >= 0:
        return int(value)
    raise ValueError(f"{field_name}: введите целое число, «-» или «{SKIP_TEXT}».")


def _parse_url_or_skip(raw_value: str) -> str | None:
    value = raw_value.strip()
    if value == SKIP_TEXT or not value:
        return None

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value

    raise ValueError("Ссылка должна начинаться с http:// или https:// и содержать домен.")


@router.message(Command("cancel"), StateFilter(PropertyCreateStates))
@router.message(F.text == CANCEL_TEXT, StateFilter(PropertyCreateStates))
async def cancel_property_creation(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добавление объекта отменено.", reply_markup=get_properties_menu_keyboard())


@router.message(F.text == ADD_PROPERTY_TEXT)
async def start_property_create(message: Message, state: FSMContext, auth_service: AuthService, property_service: PropertyService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    if not property_service.can_create_property(user):
        await message.answer("У вас нет прав на создание объектов.")
        return

    await state.clear()
    await state.set_state(PropertyCreateStates.title)
    await message.answer("Введите название объекта.", reply_markup=get_property_cancel_keyboard())


@router.message(PropertyCreateStates.title)
async def process_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым. Введите название объекта.")
        return

    await state.update_data(title=title)
    await state.set_state(PropertyCreateStates.property_type)
    await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())


@router.message(PropertyCreateStates.property_type)
async def process_property_type(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    property_type = PROPERTY_TYPE_MAP.get(value)
    if property_type is None:
        await message.answer("Выберите тип недвижимости с помощью кнопок.", reply_markup=get_property_type_keyboard())
        return

    await state.update_data(property_type=property_type.value)
    await state.set_state(PropertyCreateStates.district)
    await message.answer("Введите район.")


@router.message(PropertyCreateStates.district)
async def process_district(message: Message, state: FSMContext) -> None:
    district = (message.text or "").strip()
    if not district:
        await message.answer("Район не должен быть пустым. Введите район.")
        return

    await state.update_data(district=district)
    await state.set_state(PropertyCreateStates.address)
    await message.answer("Введите адрес.")


@router.message(PropertyCreateStates.address)
async def process_address(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()
    if not address:
        await message.answer("Адрес не должен быть пустым. Введите адрес.")
        return

    await state.update_data(address=address)
    await state.set_state(PropertyCreateStates.owner_phone)
    await message.answer("Введите номер владельца объекта.")


@router.message(PropertyCreateStates.owner_phone)
async def process_owner_phone(message: Message, state: FSMContext) -> None:
    try:
        owner_phone = normalize_owner_phone(message.text or "")
    except ValueError as error:
        await message.answer(f"{error}")
        return

    await state.update_data(owner_phone=owner_phone)
    await state.set_state(PropertyCreateStates.price)
    await message.answer("Введите цену (только число).")


@router.message(PropertyCreateStates.price)
async def process_price(message: Message, state: FSMContext) -> None:
    try:
        price = parse_money(message.text or "")
    except ValueError as error:
        await message.answer(f"{error}")
        return

    await state.update_data(price=str(price))
    await state.set_state(PropertyCreateStates.area)
    await message.answer("Введите площадь в м² (только число).")


@router.message(PropertyCreateStates.area)
async def process_area(message: Message, state: FSMContext) -> None:
    try:
        area = parse_money(message.text or "")
    except ValueError as error:
        await message.answer(f"{error}")
        return

    await state.update_data(area=str(area))
    await state.set_state(PropertyCreateStates.rooms)
    await message.answer(
        f"Введите количество комнат (число), «-» или «{SKIP_TEXT}».",
        reply_markup=get_property_skip_cancel_keyboard(),
    )


@router.message(PropertyCreateStates.rooms)
async def process_rooms(message: Message, state: FSMContext) -> None:
    try:
        rooms = _parse_positive_int_or_skip(message.text or "", "Комнаты")
    except ValueError as error:
        await message.answer(f"{error}")
        return

    await state.update_data(rooms=rooms)
    await state.set_state(PropertyCreateStates.floor)
    await message.answer(
        f"Введите этаж (число), «-» или «{SKIP_TEXT}».",
        reply_markup=get_property_skip_cancel_keyboard(),
    )


@router.message(PropertyCreateStates.floor)
async def process_floor(message: Message, state: FSMContext) -> None:
    try:
        floor = _parse_positive_int_or_skip(message.text or "", "Этаж")
    except ValueError as error:
        await message.answer(f"{error}")
        return

    await state.update_data(floor=floor)
    data = await state.get_data()
    property_type = PropertyType(data["property_type"])
    if property_type == PropertyType.APARTMENT:
        await state.set_state(PropertyCreateStates.building_floors)
        await message.answer("Введите этажность здания (положительное число).")
        return

    await state.set_state(PropertyCreateStates.description)
    await message.answer("Введите описание (или «Пропустить»).", reply_markup=get_property_skip_cancel_keyboard())


@router.message(PropertyCreateStates.building_floors)
async def process_building_floors(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not value.isdigit() or int(value) <= 0:
        await message.answer("Этажность здания должна быть положительным целым числом.")
        return

    building_floors = int(value)
    data = await state.get_data()
    floor = data.get("floor")
    if floor is not None and floor > building_floors:
        await message.answer("Этаж объекта не может быть больше этажности здания.")
        return

    await state.update_data(building_floors=building_floors)
    await state.set_state(PropertyCreateStates.description)
    await message.answer("Введите описание (или «Пропустить»).", reply_markup=get_property_skip_cancel_keyboard())


@router.message(PropertyCreateStates.description)
async def process_description(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    description = None if value == SKIP_TEXT else value

    await state.update_data(description=description)
    await state.set_state(PropertyCreateStates.link)
    await message.answer("Введите ссылку (или «Пропустить»).", reply_markup=get_property_skip_cancel_keyboard())


@router.message(PropertyCreateStates.link)
async def process_link(message: Message, state: FSMContext) -> None:
    try:
        link = _parse_url_or_skip(message.text or "")
    except ValueError as error:
        await message.answer(f"{error}")
        return

    await state.update_data(link=link)
    await state.set_state(PropertyCreateStates.status)
    await message.answer("Выберите статус объекта:", reply_markup=get_property_status_keyboard())


@router.message(PropertyCreateStates.status)
async def process_status(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    property_service: PropertyService,
    session: AsyncSession,
) -> None:
    value = (message.text or "").strip()
    status = PROPERTY_STATUS_MAP.get(value)
    if status is None:
        await message.answer("Выберите статус с помощью кнопок.", reply_markup=get_property_status_keyboard())
        return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    data = await state.get_data()

    dto = CreatePropertyDTO(
        title=data["title"],
        property_type=PropertyType(data["property_type"]),
        district=data["district"],
        address=data["address"],
        owner_phone=data["owner_phone"],
        price=Decimal(data["price"]),
        area=Decimal(data["area"]),
        rooms=data.get("rooms"),
        floor=data.get("floor"),
        building_floors=data.get("building_floors"),
        description=data.get("description"),
        link=data.get("link"),
        status=PropertyStatus(status.value),
        manager_id=user.id,
    )

    try:
        property_obj = await property_service.create_property(current_user=user, data=dto)
    except PermissionError as error:
        await message.answer(str(error), reply_markup=get_properties_menu_keyboard())
        await state.clear()
        return
    except ValueError as error:
        await message.answer(str(error))
        return

    await session.commit()
    await state.clear()

    manager_name = property_obj.manager.full_name if property_obj.manager else user.full_name
    await message.answer(
        format_property_created_card(property_obj=property_obj, manager_name=manager_name),
        reply_markup=get_properties_menu_keyboard(),
    )


@router.message(StateFilter(PropertyCreateStates))
async def fallback_in_state(message: Message) -> None:
    await message.answer("Используйте предложенные кнопки или введите корректное значение.")


@router.message(F.text == "Добавить объект")
async def start_alias(message: Message, state: FSMContext, auth_service: AuthService, property_service: PropertyService) -> None:
    await start_property_create(message, state, auth_service, property_service)