from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import (
    ADD_CLIENT_TEXT,
    CANCEL_TEXT,
    SKIP_TEXT,
    SOURCE_OPTIONS,
    get_cancel_keyboard,
    get_clients_menu_keyboard,
    get_property_type_keyboard,
    get_request_type_keyboard,
    get_skip_cancel_keyboard,
    get_source_keyboard,
)
from app.bot.states.clients import ClientCreateStates
from app.common.dto.clients import CreateClientDTO
from app.common.enums import PropertyType, RequestType
from app.common.formatters.client_formatter import format_client_created_card
from app.common.utils.parsers import normalize_phone, parse_money, parse_next_contact_at
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


@router.message(Command("cancel"), ClientCreateStates)
@router.message(F.text == CANCEL_TEXT, ClientCreateStates)
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
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ClientCreateStates.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    full_name = (message.text or "").strip()
    if not full_name:
        await message.answer("ФИО не должно быть пустым. Введите ФИО клиента.")
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
    await message.answer("Введите район (или нажмите «Пропустить»).", reply_markup=get_skip_cancel_keyboard())


@router.message(ClientCreateStates.district)
async def process_district(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    district = None if value == SKIP_TEXT else value

    await state.update_data(district=district)
    await state.set_state(ClientCreateStates.rooms)
    await message.answer(
        "Введите количество комнат (целое число). Допустимо значение «Студия».",
        reply_markup=get_skip_cancel_keyboard(),
    )


@router.message(ClientCreateStates.rooms)
async def process_rooms(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if value == SKIP_TEXT:
        await state.update_data(rooms=None)
    elif value.lower() == "студия":
        await state.update_data(rooms=None, rooms_note="Студия")
    elif value.isdigit() and int(value) > 0:
        await state.update_data(rooms=int(value))
    else:
        await message.answer("Комнаты: введите число > 0, «Студия» или «Пропустить».")
        return

    await state.set_state(ClientCreateStates.budget_min)
    await message.answer("Введите минимальный бюджет (только число).", reply_markup=get_skip_cancel_keyboard())


@router.message(ClientCreateStates.budget_min)
async def process_budget_min(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if value == SKIP_TEXT:
        await state.update_data(budget_min=None)
    else:
        try:
            budget_min = parse_money(value)
        except ValueError as error:
            await message.answer(f"{error}")
            return
        await state.update_data(budget_min=str(budget_min))

    await state.set_state(ClientCreateStates.budget_max)
    await message.answer("Введите максимальный бюджет (только число).", reply_markup=get_skip_cancel_keyboard())


@router.message(ClientCreateStates.budget_max)
async def process_budget_max(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    data = await state.get_data()

    budget_min: Decimal | None = None
    if data.get("budget_min") is not None:
        budget_min = Decimal(data["budget_min"])

    if value == SKIP_TEXT:
        budget_max = None
    else:
        try:
            budget_max = parse_money(value)
        except ValueError as error:
            await message.answer(f"{error}")
            return

    if budget_min is not None and budget_max is not None and budget_max < budget_min:
        await message.answer("Максимальный бюджет не может быть меньше минимального.")
        return

    await state.update_data(budget_max=str(budget_max) if budget_max is not None else None)
    await state.set_state(ClientCreateStates.note)
    await message.answer("Введите заметку по клиенту (или нажмите «Пропустить»).", reply_markup=get_skip_cancel_keyboard())


@router.message(ClientCreateStates.note)
async def process_note(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    note = None if value == SKIP_TEXT else value
    await state.update_data(note=note)

    await state.set_state(ClientCreateStates.next_contact_at)
    await message.answer(
        "Введите дату следующего контакта в формате ДД.ММ.ГГГГ или ДД.ММ.ГГГГ ЧЧ:ММ (или «Пропустить»).",
        reply_markup=get_skip_cancel_keyboard(),
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
        try:
            next_contact_at = parse_next_contact_at(value)
        except ValueError as error:
            await message.answer(f"{error}")
            return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    data = await state.get_data()
    final_note = data.get("note")
    if data.get("rooms_note"):
        final_note = f"{final_note}\nТип комнат: {data['rooms_note']}" if final_note else f"Тип комнат: {data['rooms_note']}"

    dto = CreateClientDTO(
        full_name=data["full_name"],
        phone=data["phone"],
        source=data.get("source"),
        request_type=RequestType(data["request_type"]),
        property_type=PropertyType(data["property_type"]),
        district=data.get("district"),
        rooms=data.get("rooms"),
        budget_min=Decimal(data["budget_min"]) if data.get("budget_min") else None,
        budget_max=Decimal(data["budget_max"]) if data.get("budget_max") else None,
        note=final_note,
        next_contact_at=next_contact_at,
        manager_id=user.id,
    )

    client = await client_service.create_client(dto)
    await session.commit()
    await state.clear()

    await message.answer(
        format_client_created_card(client=client, manager_name=user.full_name),
        reply_markup=get_clients_menu_keyboard(),
    )


@router.message(ClientCreateStates)
async def fallback_in_state(message: Message) -> None:
    await message.answer("Используйте предложенные кнопки или введите корректное значение.")


@router.message(F.text == "Добавить клиента")
async def start_alias(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    await start_client_create(message, state, auth_service)