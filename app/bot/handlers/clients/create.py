from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import (
    ADD_CLIENT_TEXT,
    CANCEL_TEXT,
    NEXT_CONTACT_QUICK_OPTIONS,
    ROOMS_OPTIONS,
    SKIP_TEXT,
    UNKNOWN_TEXT,
    SOURCE_OPTIONS,
    WALL_MATERIAL_OPTIONS,
    get_building_floors_keyboard,
    get_clients_menu_keyboard,
    get_district_keyboard,
    get_floor_keyboard,
    get_full_name_keyboard,
    get_next_contact_keyboard,
    get_property_type_keyboard,
    get_request_type_keyboard,
    get_rooms_keyboard,
    get_skip_cancel_keyboard,
    get_source_keyboard,
    get_wall_material_keyboard,
    get_year_built_keyboard,
)
from app.bot.states.clients import ClientCreateStates
from app.common.dto.clients import CreateClientDTO
from app.common.enums import PropertyType, RequestType, WallMaterial
from app.common.formatters.client_formatter import format_client_created_card
from app.common.utils.parsers import (
    normalize_phone,
    parse_int_in_range,
    parse_money,
    parse_next_contact_at,
    parse_year_built,
)
from app.services.auth_service import AuthService
from app.services.clients import ClientService

router = Router(name="client_create")

REQUEST_TYPE_MAP: dict[str, RequestType] = {
    "Купить": RequestType.BUY,
    "Продать": RequestType.SELL,
    "Снять": RequestType.RENT,
    "Сдать": RequestType.RENT_OUT,
}

PROPERTY_TYPE_MAP: dict[str, PropertyType] = {
    "Квартира": PropertyType.APARTMENT,
    "Дом": PropertyType.HOUSE,
    "Коммерческая": PropertyType.COMMERCIAL,
    "Участок": PropertyType.LAND,
}

WALL_MATERIAL_MAP: dict[str, WallMaterial] = {
    "Кирпич": WallMaterial.BRICK,
    "Панель": WallMaterial.PANEL,
    "Монолит": WallMaterial.MONOLITH,
}


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


@router.message(Command("cancel"), StateFilter(ClientCreateStates))
@router.message(F.text == CANCEL_TEXT, StateFilter(ClientCreateStates))
async def cancel_client_creation(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добавление клиента отменено.", reply_markup=get_clients_menu_keyboard())


@router.message(F.text == ADD_CLIENT_TEXT)
async def start_client_create(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await state.clear()
    await state.set_state(ClientCreateStates.full_name)
    await message.answer(
        "Введите ФИО клиента.",
        reply_markup=get_full_name_keyboard(),
    )


@router.message(ClientCreateStates.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    raw_value = (message.text or "").strip()
    full_name = UNKNOWN_TEXT if raw_value == UNKNOWN_TEXT else raw_value
    if not full_name:
        await message.answer("ФИО не должно быть пустым. Введите ФИО клиента или нажмите «Неизвестно».")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(ClientCreateStates.phone)
    await message.answer("Введите телефон клиента (например, +79991234567).")


@router.message(ClientCreateStates.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    try:
        phone = normalize_phone(message.text or "")
    except ValueError as error:
        await message.answer(f"{error}\nВведите телефон в корректном формате.")
        return

    await state.update_data(phone=phone)
    await state.set_state(ClientCreateStates.source)
    await message.answer("Выберите источник клиента:", reply_markup=get_source_keyboard())


@router.message(ClientCreateStates.source)
async def process_source(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if value not in SOURCE_OPTIONS:
        await message.answer("Выберите источник с помощью кнопок.", reply_markup=get_source_keyboard())
        return

    await state.update_data(source=value)
    await state.set_state(ClientCreateStates.request_type)
    await message.answer("Выберите тип запроса:", reply_markup=get_request_type_keyboard())


@router.message(ClientCreateStates.request_type)
async def process_request_type(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    request_type = REQUEST_TYPE_MAP.get(value)
    if request_type is None:
        await message.answer("Выберите тип запроса с помощью кнопок.", reply_markup=get_request_type_keyboard())
        return

    await state.update_data(request_type=request_type.value)
    await state.set_state(ClientCreateStates.property_type)
    await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())


@router.message(ClientCreateStates.property_type)
async def process_property_type(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    property_type = PROPERTY_TYPE_MAP.get(value)
    if property_type is None:
        await message.answer("Выберите тип недвижимости с помощью кнопок.", reply_markup=get_property_type_keyboard())
        return

    await state.update_data(property_type=property_type.value)
    await state.set_state(ClientCreateStates.district)
    await message.answer("Выберите район кнопкой или введите вручную.", reply_markup=get_district_keyboard())


@router.message(ClientCreateStates.district)
async def process_district(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not value:
        await message.answer("Район не должен быть пустым. Выберите кнопкой или введите текстом.",
                             reply_markup=get_district_keyboard())
        return

    district = None if value == SKIP_TEXT else value

    await state.update_data(district=district)
    await state.set_state(ClientCreateStates.rooms)
    await message.answer(
        "Выберите количество комнат кнопкой или введите вручную (1-5, Студия).",
        reply_markup=get_rooms_keyboard(),
    )


@router.message(ClientCreateStates.rooms)
async def process_rooms(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if value == SKIP_TEXT:
        await state.update_data(rooms=None)
    elif value.lower() == "студия":
        await state.update_data(rooms="Студия")
    elif value in ROOMS_OPTIONS:
        await state.update_data(rooms=value)
    elif value.isdigit() and 0 < int(value) <= 50:
        await state.update_data(rooms=value)
    else:
        await message.answer("Комнаты: выберите 1-5, «Студия», «Пропустить» или введите число вручную.")
        return

    await state.set_state(ClientCreateStates.budget)
    await message.answer("Введите цену (только число) или нажмите «Пропустить».",
                         reply_markup=get_skip_cancel_keyboard())


@router.message(ClientCreateStates.budget)
async def process_budget(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if value == SKIP_TEXT:
        await state.update_data(budget=None)
    else:
        try:
            budget = parse_money(value)
        except ValueError as error:
            await message.answer(f"{error}")
            return
        await state.update_data(budget=str(budget))

    data = await state.get_data()
    property_type = PropertyType(data["property_type"])
    if property_type == PropertyType.APARTMENT:
        await state.set_state(ClientCreateStates.floor)
        await message.answer(
            "Выберите этаж (1-16) кнопкой или введите вручную.",
            reply_markup=get_floor_keyboard(),
        )
        return

    await state.update_data(floor=None, building_floors=None, wall_material=None, year_built=None)
    await state.set_state(ClientCreateStates.note)
    await message.answer("Введите заметку по клиенту (или нажмите «Пропустить»).",
                         reply_markup=get_skip_cancel_keyboard())


@router.message(ClientCreateStates.floor)
async def process_floor(message: Message, state: FSMContext) -> None:
    try:
        floor = parse_int_in_range(message.text or "", field_name="Этаж", minimum=1, maximum=16)
    except ValueError as error:
        await message.answer(
            f"{error}\nВыберите этаж кнопкой 1-16 или введите вручную.",
            reply_markup=get_floor_keyboard(),
        )
        return

    await state.update_data(floor=floor)
    await state.set_state(ClientCreateStates.building_floors)
    await message.answer(
        "Выберите этажность дома (1-16) кнопкой или введите вручную.",
        reply_markup=get_building_floors_keyboard(),
    )


@router.message(ClientCreateStates.building_floors)
async def process_building_floors(message: Message, state: FSMContext) -> None:
    try:
        building_floors = parse_int_in_range(message.text or "", field_name="Этажность дома", minimum=1, maximum=16)
    except ValueError as error:
        await message.answer(
            f"{error}\nВыберите этажность кнопкой 1-16 или введите вручную.",
            reply_markup=get_building_floors_keyboard(),
        )
        return

    data = await state.get_data()
    floor = data.get("floor")
    if floor is not None and floor > building_floors:
        await message.answer(
            "Этаж не может быть больше этажности дома. Введите этажность повторно.",
            reply_markup=get_building_floors_keyboard(),
        )
        return

    await state.update_data(building_floors=building_floors)
    await state.set_state(ClientCreateStates.wall_material)
    await message.answer("Выберите материал стен:", reply_markup=get_wall_material_keyboard())


@router.message(ClientCreateStates.wall_material)
async def process_wall_material(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    wall_material = WALL_MATERIAL_MAP.get(value)
    if wall_material is None:
        await message.answer(
            f"Выберите материал стен кнопкой ({', '.join(WALL_MATERIAL_OPTIONS)}).",
            reply_markup=get_wall_material_keyboard(),
        )
        return

    await state.update_data(wall_material=wall_material.value)
    await state.set_state(ClientCreateStates.year_built)
    await message.answer(
        "Введите год постройки (например, 2012) или нажмите «Пропустить».",
        reply_markup=get_year_built_keyboard(),
    )


@router.message(ClientCreateStates.year_built)
async def process_year_built(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if value == SKIP_TEXT:
        await state.update_data(year_built=None)
    else:
        try:
            year_built = parse_year_built(value)
        except ValueError as error:
            await message.answer(f"{error}\nВведите корректный год или нажмите «Пропустить».",
                                 reply_markup=get_year_built_keyboard())
            return
        await state.update_data(year_built=year_built)

    await state.set_state(ClientCreateStates.note)
    await message.answer("Введите заметку по клиенту (или нажмите «Пропустить»).", reply_markup=get_skip_cancel_keyboard())


@router.message(ClientCreateStates.note)
async def process_note(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    note = None if value == SKIP_TEXT else value
    await state.update_data(note=note)

    await state.set_state(ClientCreateStates.next_contact_at)
    await message.answer(
        "Введите дату следующего контакта: кнопкой (Сегодня/Завтра/Послезавтра) "
        "или вручную в формате ДД ММ ГГГГ (например, 03 08 2026).",
        reply_markup=get_next_contact_keyboard(),
    )


@router.message(ClientCreateStates.next_contact_at)
async def process_next_contact_at(
    message: Message,
    state: FSMContext,
    client_service: ClientService,
    auth_service: AuthService,
    session: AsyncSession,
) -> None:
    value = (message.text or "").strip()

    next_contact_at = None
    if value != SKIP_TEXT:
        if value in NEXT_CONTACT_QUICK_OPTIONS:
            days_offset = NEXT_CONTACT_QUICK_OPTIONS.index(value)
            target_date = (datetime.now(tz=timezone.utc) + timedelta(days=days_offset)).date()
            next_contact_at = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        else:
            try:
                next_contact_at = parse_next_contact_at(value)
            except ValueError as error:
                await message.answer(
                    f"{error}\nПопробуйте снова: «Сегодня», «Завтра», «Послезавтра» или дату в формате 03 08 2026.",
                    reply_markup=get_next_contact_keyboard(),
                )
                return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    data = await state.get_data()

    dto = CreateClientDTO(
        full_name=data["full_name"],
        phone=data["phone"],
        source=data.get("source"),
        request_type=RequestType(data["request_type"]),
        property_type=PropertyType(data["property_type"]),
        district=data.get("district"),
        rooms=data.get("rooms"),
        budget=Decimal(data["budget"]) if data.get("budget") else None,
        floor=data.get("floor"),
        building_floors=data.get("building_floors"),
        wall_material=WallMaterial(data["wall_material"]) if data.get("wall_material") else None,
        year_built=data.get("year_built"),
        note=data.get("note"),
        next_contact_at=next_contact_at,
        manager_id=user.id,
    )

    create_result = await client_service.create_client(dto)
    if isinstance(create_result, tuple):
        client, linked_properties_count = create_result
    else:
        client = create_result
        linked_properties_count = 0
    await session.commit()
    await state.clear()

    await message.answer(
        format_client_created_card(client=client, manager_name=user.full_name),
        reply_markup=get_clients_menu_keyboard(),
    )
    if linked_properties_count > 0:
        await message.answer(
            f"🔗 Найдено {linked_properties_count} объектов по совпадающему номеру. "
            "Связи созданы автоматически.",
        )


@router.message(StateFilter(ClientCreateStates))
async def fallback_in_state(message: Message) -> None:
    await message.answer("Используйте предложенные кнопки или введите корректное значение.")


@router.message(F.text == "Добавить клиента")
async def start_alias(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    await start_client_create(message, state, auth_service)