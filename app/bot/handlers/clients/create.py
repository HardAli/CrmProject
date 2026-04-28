from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.clients.photo_media_group import buffer_media_group_photo
from app.bot.keyboards.clients import (
    ADD_CLIENT_TEXT,
    CANCEL_TEXT,
    DONE_TEXT,
    NEXT_CONTACT_QUICK_OPTIONS,
    ROOMS_OPTIONS,
    SKIP_TEXT,
    UNKNOWN_TEXT,
    SOURCE_OPTIONS,
    WALL_MATERIAL_OPTIONS,
    get_building_floors_keyboard,
    get_client_card_actions_keyboard,
    get_client_create_photo_keyboard,
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
from app.database.session import session_scope
from app.repositories.client_photo_repository import ClientPhotoRepository
from app.repositories.clients import ClientRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.client_photo_service import ClientPhotoService
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


async def _show_client_card_after_photo_step(
    *,
    message: Message,
    client_id: int | None,
    user,
    client_service: ClientService,
) -> None:
    if not isinstance(client_id, int):
        await message.answer("Клиент не найден.")
        return

    client = await client_service.get_client_for_view(current_user=user, client_id=client_id)
    if client is None:
        await message.answer("Клиент не найден.")
        return

    manager_name = client.manager.full_name if client.manager else "—"
    await message.answer(
        format_client_created_card(client=client, manager_name=manager_name),
        reply_markup=get_client_card_actions_keyboard(
            client_id=client.id,
            can_edit=client_service.can_edit_client(current_user=user, client=client),
        ),
    )


async def _save_client_photos_with_new_session(
    *,
    telegram_user_id: int,
    client_id: int,
    photos: list[tuple[str, str | None]],
) -> tuple[int, int]:
    async with session_scope() as inner_session:
        user_repository = UserRepository(inner_session)
        auth_service = AuthService(user_repository=user_repository)
        current_user = await auth_service.get_active_user_by_telegram_id(telegram_user_id)
        if current_user is None:
            return 0, 0

        client_photo_service = ClientPhotoService(
            client_photo_repository=ClientPhotoRepository(session=inner_session),
            client_repository=ClientRepository(session=inner_session),
        )
        saved_count, duplicate_count = await client_photo_service.add_client_photos_bulk(
            current_user=current_user,
            client_id=client_id,
            photos=photos,
        )
        await inner_session.commit()
        return saved_count, duplicate_count


@router.message(
    Command("cancel"),
    StateFilter(
        ClientCreateStates.full_name,
        ClientCreateStates.phone,
        ClientCreateStates.source,
        ClientCreateStates.request_type,
        ClientCreateStates.property_type,
        ClientCreateStates.district,
        ClientCreateStates.rooms,
        ClientCreateStates.budget,
        ClientCreateStates.floor,
        ClientCreateStates.building_floors,
        ClientCreateStates.wall_material,
        ClientCreateStates.year_built,
        ClientCreateStates.note,
        ClientCreateStates.next_contact_at,
    ),
)
@router.message(
    F.text == CANCEL_TEXT,
    StateFilter(
        ClientCreateStates.full_name,
        ClientCreateStates.phone,
        ClientCreateStates.source,
        ClientCreateStates.request_type,
        ClientCreateStates.property_type,
        ClientCreateStates.district,
        ClientCreateStates.rooms,
        ClientCreateStates.budget,
        ClientCreateStates.floor,
        ClientCreateStates.building_floors,
        ClientCreateStates.wall_material,
        ClientCreateStates.year_built,
        ClientCreateStates.note,
        ClientCreateStates.next_contact_at,
    ),
)
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
    if not raw_value:
        await message.answer("ФИО не должно быть пустым. Введите ФИО клиента или нажмите «Неизвестно».")
        return

    full_name_is_unknown = raw_value == UNKNOWN_TEXT
    if full_name_is_unknown:
        await state.update_data(full_name=None, full_name_is_unknown=True)
    else:
        await state.update_data(full_name=raw_value, full_name_is_unknown=False)

    await state.set_state(ClientCreateStates.phone)
    await message.answer("Введите телефон клиента (например, +79991234567).")


@router.message(ClientCreateStates.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    try:
        phone = normalize_phone(message.text or "")
    except ValueError as error:
        await message.answer(f"{error}\nВведите телефон в корректном формате.")
        return

    data = await state.get_data()
    update_data: dict[str, object] = {"phone": phone}
    if data.get("full_name_is_unknown"):
        update_data["full_name"] = phone

    await state.update_data(**update_data)
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

    full_name = data["phone"] if data.get("full_name_is_unknown") else data["full_name"]

    dto = CreateClientDTO(
        full_name=full_name,
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
    await state.update_data(created_client_id=client.id)
    await state.set_state(ClientCreateStates.waiting_for_photos_after_create)

    await message.answer(
        "Клиент создан.\n\n"
        "Теперь отправьте фотографии клиента.\n"
        "Можно отправить одну фотографию или сразу пачку до 10 фото.\n\n"
        "Если фото не нужны, нажмите «Пропустить».",
        reply_markup=get_client_create_photo_keyboard(),
    )
    if linked_properties_count > 0:
        await message.answer(
            f"🔗 Найдено {linked_properties_count} объектов по совпадающему номеру. "
            "Связи созданы автоматически.",
        )


@router.message(F.text == SKIP_TEXT, ClientCreateStates.waiting_for_photos_after_create)
async def skip_photos_after_create(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    state_data = await state.get_data()
    client_id = state_data.get("created_client_id")
    await state.clear()

    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await message.answer("Клиент создан без фотографий.")
    await _show_client_card_after_photo_step(
        message=message,
        client_id=client_id,
        user=user,
        client_service=client_service,
    )


@router.message(Command("done"), ClientCreateStates.waiting_for_photos_after_create)
@router.message(F.text == DONE_TEXT, ClientCreateStates.waiting_for_photos_after_create)
async def done_photos_after_create(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    state_data = await state.get_data()
    client_id = state_data.get("created_client_id")
    await state.clear()

    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await message.answer("Клиент создан. Фото сохранены.")
    await _show_client_card_after_photo_step(
        message=message,
        client_id=client_id,
        user=user,
        client_service=client_service,
    )


@router.message(Command("cancel"), ClientCreateStates.waiting_for_photos_after_create)
@router.message(F.text == CANCEL_TEXT, ClientCreateStates.waiting_for_photos_after_create)
async def cancel_photo_step_after_create(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    state_data = await state.get_data()
    client_id = state_data.get("created_client_id")
    await state.clear()

    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await message.answer("Добавление фото отменено. Клиент уже создан.")
    await _show_client_card_after_photo_step(
        message=message,
        client_id=client_id,
        user=user,
        client_service=client_service,
    )


@router.message(ClientCreateStates.waiting_for_photos_after_create)
async def save_photo_after_create(
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

    state_data = await state.get_data()
    client_id = state_data.get("created_client_id")
    if not isinstance(client_id, int):
        await state.clear()
        await message.answer("Клиент не найден.")
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

    if not message.photo:
        await message.answer(
            "Отправьте фото клиента или нажмите «Пропустить».",
            reply_markup=get_client_create_photo_keyboard(),
        )
        return

    photo = message.photo[-1]
    file_id = photo.file_id
    file_unique_id = photo.file_unique_id

    if message.media_group_id:
        async def on_media_group_ready(photos: list[tuple[str, str | None]]) -> None:
            try:
                saved_count, duplicate_count = await _save_client_photos_with_new_session(
                    telegram_user_id=message.from_user.id,
                    client_id=client_id,
                    photos=photos,
                )
            except (PermissionError, ValueError):
                await state.clear()
                await message.answer("Клиент не найден.")
                return
            except Exception:
                await message.answer("Не удалось сохранить фотографии. Попробуйте позже.")
                return

            if duplicate_count:
                await message.answer(
                    f"Сохранено фото: {saved_count}. Дубликатов пропущено: {duplicate_count}. "
                    "Можете отправить ещё фото или нажать «Готово».",
                    reply_markup=get_client_create_photo_keyboard(),
                )
                return

            await message.answer(
                f"Сохранено фото: {saved_count}. Можете отправить ещё фото или нажать «Готово».",
                reply_markup=get_client_create_photo_keyboard(),
            )

        key = f"client_create_photo:{client_id}:{message.from_user.id}:{message.media_group_id}"
        await buffer_media_group_photo(
            key=key,
            photo=(file_id, file_unique_id),
            on_ready=on_media_group_ready,
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
            "Сохранено фото: 0. Дубликатов пропущено: 1. Можете отправить ещё фото или нажать «Готово».",
            reply_markup=get_client_create_photo_keyboard(),
        )
        return

    await message.answer(
        "Фото сохранено. Можете отправить ещё фото или нажать «Готово».",
        reply_markup=get_client_create_photo_keyboard(),
    )


@router.message(StateFilter(ClientCreateStates))
async def fallback_in_state(message: Message) -> None:
    await message.answer("Используйте предложенные кнопки или введите корректное значение.")


@router.message(F.text == "Добавить клиента")
async def start_alias(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    await start_client_create(message, state, auth_service)
