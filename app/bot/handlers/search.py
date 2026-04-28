from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.clients import CANCEL_TEXT, SKIP_TEXT, get_clients_list_inline_keyboard
from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.properties import get_properties_list_inline_keyboard
from app.bot.keyboards.search import (
    ADVANCED_CLIENT_SEARCH_TEXT,
    ADVANCED_PROPERTY_SEARCH_TEXT,
    QUICK_CLIENT_SEARCH_TEXT,
    QUICK_PROPERTY_SEARCH_TEXT,
    SEARCH_MENU_TEXT,
    get_client_search_request_type_keyboard,
    get_client_search_status_keyboard,
    get_property_search_status_keyboard,
    get_property_search_type_keyboard,
    get_search_cancel_keyboard,
    get_search_menu_keyboard,
    get_search_skip_cancel_keyboard,
)
from app.bot.states.search_states import SearchStates
from app.common.enums import ClientStatus, PropertyStatus, PropertyType, RequestType
from app.common.utils.money import parse_money_range_to_tenge
from app.common.formatters.search_formatter import (
    format_client_search_applied_filters,
    format_client_search_results,
    format_property_search_applied_filters,
    format_property_search_results,
)
from app.services.auth_service import AuthService
from app.services.search import SearchService

router = Router(name="search")

CLIENT_STATUS_MAP: dict[str, ClientStatus] = {
    "Новый": ClientStatus.NEW,
    "В работе": ClientStatus.IN_PROGRESS,
    "Ждёт звонка": ClientStatus.WAITING,
    "Показ": ClientStatus.SHOWING,
    "Закрыт": ClientStatus.CLOSED_SUCCESS,
    "Отказ": ClientStatus.CLOSED_FAILED,
}

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

PROPERTY_STATUS_MAP: dict[str, PropertyStatus] = {
    "Активен": PropertyStatus.ACTIVE,
    "Продан": PropertyStatus.SOLD,
    "Сдан": PropertyStatus.RESERVED,
    "Архив": PropertyStatus.ARCHIVED,
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


@router.message(Command("search"))
@router.message(F.text == SEARCH_MENU_TEXT)
async def open_search_menu(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await state.clear()
    await state.set_state(SearchStates.choose_mode)
    await message.answer("Раздел поиска. Выберите тип поиска:", reply_markup=get_search_menu_keyboard())


@router.message(F.text == CANCEL_TEXT, StateFilter(SearchStates))
@router.message(Command("cancel"), StateFilter(SearchStates))
async def cancel_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Поиск отменён.", reply_markup=get_main_menu_keyboard())


@router.message(SearchStates.choose_mode, F.text == QUICK_CLIENT_SEARCH_TEXT)
async def choose_quick_client_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="clients")
    await state.set_state(SearchStates.client_quick_query)
    await message.answer(
        "Введите запрос для клиентов (имя / телефон / район).",
        reply_markup=get_search_cancel_keyboard(),
    )


@router.message(SearchStates.choose_mode, F.text == QUICK_PROPERTY_SEARCH_TEXT)
async def choose_quick_property_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="properties")
    await state.set_state(SearchStates.property_quick_query)
    await message.answer(
        "Введите запрос для объектов (название / район).",
        reply_markup=get_search_cancel_keyboard(),
    )


@router.message(SearchStates.choose_mode, F.text == ADVANCED_CLIENT_SEARCH_TEXT)
async def choose_advanced_client_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="clients", filters={})
    await state.set_state(SearchStates.client_full_name)
    await message.answer("Имя клиента (частично) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.choose_mode, F.text == ADVANCED_PROPERTY_SEARCH_TEXT)
async def choose_advanced_property_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="properties", filters={})
    await state.set_state(SearchStates.property_title)
    await message.answer("Название объекта (частично) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.client_quick_query)
async def run_quick_client_search(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    search_service: SearchService,
) -> None:
    query = (message.text or "").strip()
    if not query:
        await message.answer("Введите непустой запрос.")
        return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    filters = {"full_name": query, "district": query, "phone": query, "limit": SearchService.DEFAULT_LIMIT}
    try:
        clients = await search_service.search_clients(current_user=user, filters=filters)
    except ValueError as error:
        await message.answer(str(error))
        return

    await state.clear()
    if not clients:
        await message.answer("По вашему запросу клиенты не найдены.", reply_markup=get_search_menu_keyboard())
        return

    applied = format_client_search_applied_filters(filters)
    text = format_client_search_results(clients=clients, limit=SearchService.DEFAULT_LIMIT)
    await message.answer(f"{text}\n\n<b>Фильтры:</b>\n{applied}", reply_markup=get_clients_list_inline_keyboard(clients))
    await message.answer("Можно открыть карточку клиента по кнопке выше или запустить новый поиск.", reply_markup=get_search_menu_keyboard())


@router.message(SearchStates.property_quick_query)
async def run_quick_property_search(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    search_service: SearchService,
) -> None:
    query = (message.text or "").strip()
    if not query:
        await message.answer("Введите непустой запрос.")
        return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    filters = {"title": query, "district": query, "limit": SearchService.DEFAULT_LIMIT}
    try:
        properties = await search_service.search_properties(current_user=user, filters=filters)
    except ValueError as error:
        await message.answer(str(error))
        return

    await state.clear()
    if not properties:
        await message.answer("По вашему запросу объекты не найдены.", reply_markup=get_search_menu_keyboard())
        return

    applied = format_property_search_applied_filters(filters)
    text = format_property_search_results(properties=properties, limit=SearchService.DEFAULT_LIMIT)
    await message.answer(f"{text}\n\n<b>Фильтры:</b>\n{applied}", reply_markup=get_properties_list_inline_keyboard(properties))
    await message.answer("Можно открыть карточку объекта по кнопке выше или запустить новый поиск.", reply_markup=get_search_menu_keyboard())


@router.message(SearchStates.client_full_name)
async def client_filter_full_name(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "full_name", message.text)
    await state.set_state(SearchStates.client_phone)
    await message.answer("Телефон (полный или часть) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.client_phone)
async def client_filter_phone(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "phone", message.text)
    await state.set_state(SearchStates.client_district)
    await message.answer("Район (полный или часть) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.client_district)
async def client_filter_district(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "district", message.text)
    await state.set_state(SearchStates.client_status)
    await message.answer("Статус клиента или «Пропустить»:", reply_markup=get_client_search_status_keyboard())


@router.message(SearchStates.client_status)
async def client_filter_status(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == SKIP_TEXT:
        await state.set_state(SearchStates.client_request_type)
        await message.answer("Тип запроса или «Пропустить»:", reply_markup=get_client_search_request_type_keyboard())
        return

    status = CLIENT_STATUS_MAP.get(text)
    if status is None:
        await message.answer("Выберите статус кнопкой или нажмите «Пропустить».", reply_markup=get_client_search_status_keyboard())
        return

    await _save_filter(state, "status", status)
    await state.set_state(SearchStates.client_request_type)
    await message.answer("Тип запроса или «Пропустить»:", reply_markup=get_client_search_request_type_keyboard())


@router.message(SearchStates.client_request_type)
async def client_filter_request_type(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    search_service: SearchService,
) -> None:
    text = (message.text or "").strip()
    if text != SKIP_TEXT:
        request_type = REQUEST_TYPE_MAP.get(text)
        if request_type is None:
            await message.answer(
                "Выберите тип запроса кнопкой или нажмите «Пропустить».",
                reply_markup=get_client_search_request_type_keyboard(),
            )
            return
        await _save_filter(state, "request_type", request_type)

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    data = await state.get_data()
    filters = dict(data.get("filters", {}))
    filters["limit"] = SearchService.DEFAULT_LIMIT

    try:
        clients = await search_service.search_clients(current_user=user, filters=filters)
    except ValueError as error:
        await message.answer(str(error), reply_markup=get_search_menu_keyboard())
        await state.set_state(SearchStates.choose_mode)
        return

    await state.clear()
    if not clients:
        await message.answer("По выбранным фильтрам клиенты не найдены.", reply_markup=get_search_menu_keyboard())
        return

    text_result = format_client_search_results(clients=clients, limit=SearchService.DEFAULT_LIMIT)
    applied = format_client_search_applied_filters(filters)
    await message.answer(f"{text_result}\n\n<b>Фильтры:</b>\n{applied}", reply_markup=get_clients_list_inline_keyboard(clients))
    await message.answer("Поиск завершён. Можно запустить новый поиск.", reply_markup=get_search_menu_keyboard())


@router.message(SearchStates.property_title)
async def property_filter_title(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "title", message.text)
    await state.set_state(SearchStates.property_district)
    await message.answer("Район (полный или часть) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.property_district)
async def property_filter_district(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "district", message.text)
    await state.set_state(SearchStates.property_type)
    await message.answer("Тип недвижимости или «Пропустить»:", reply_markup=get_property_search_type_keyboard())


@router.message(SearchStates.property_type)
async def property_filter_type(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == SKIP_TEXT:
        await state.set_state(SearchStates.property_status)
        await message.answer("Статус объекта или «Пропустить»:", reply_markup=get_property_search_status_keyboard())
        return

    property_type = PROPERTY_TYPE_MAP.get(text)
    if property_type is None:
        await message.answer("Выберите тип кнопкой или «Пропустить».", reply_markup=get_property_search_type_keyboard())
        return

    await _save_filter(state, "property_type", property_type)
    await state.set_state(SearchStates.property_status)
    await message.answer("Статус объекта или «Пропустить»:", reply_markup=get_property_search_status_keyboard())


@router.message(SearchStates.property_status)
async def property_filter_status(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == SKIP_TEXT:
        await state.set_state(SearchStates.property_price_min)
        await message.answer("Минимальная цена или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())
        return

    status = PROPERTY_STATUS_MAP.get(text)
    if status is None:
        await message.answer("Выберите статус кнопкой или «Пропустить».", reply_markup=get_property_search_status_keyboard())
        return

    await _save_filter(state, "status", status)
    await state.set_state(SearchStates.property_price_min)
    await message.answer("Минимальная цена или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.property_price_min)
async def property_filter_price_min(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text != SKIP_TEXT:
        value_min, value_max = parse_money_range_to_tenge(text)
        if value_min is None and value_max is None:
            await message.answer("Введите цену, например 19.5, от 20, до 25 или 15-25.")
            return

        if value_min is not None:
            await _save_filter(state, "price_min", value_min)
        if value_max is not None:
            await _save_filter(state, "price_max", value_max)

        if value_max is not None:
            await state.set_state(SearchStates.property_rooms)
            await message.answer("Количество комнат или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())
            return

    await state.set_state(SearchStates.property_price_max)
    await message.answer("Максимальная цена или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.property_price_max)
async def property_filter_price_max(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text != SKIP_TEXT:
        _, value_max = parse_money_range_to_tenge(f"до {text}" if "до" not in text.lower() else text)
        if value_max is None:
            await message.answer("Введите цену, например 25 или 19.5 млн, либо «Пропустить».")
            return
        await _save_filter(state, "price_max", value_max)

    await state.set_state(SearchStates.property_rooms)
    await message.answer("Количество комнат или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.property_rooms)
async def property_filter_rooms(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    search_service: SearchService,
) -> None:
    text = (message.text or "").strip()
    if text != SKIP_TEXT:
        if text.lower() == "студия":
            await _save_filter(state, "rooms", "Студия")
        elif text.isdigit() and int(text) > 0:
            await _save_filter(state, "rooms", text)
        else:
            await message.answer("Введите целое число больше 0, «Студия» или «Пропустить».")
            return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    data = await state.get_data()
    filters = dict(data.get("filters", {}))
    filters["limit"] = SearchService.DEFAULT_LIMIT

    try:
        properties = await search_service.search_properties(current_user=user, filters=filters)
    except ValueError as error:
        await message.answer(str(error), reply_markup=get_search_menu_keyboard())
        await state.set_state(SearchStates.choose_mode)
        return

    await state.clear()
    if not properties:
        await message.answer("По выбранным фильтрам объекты не найдены.", reply_markup=get_search_menu_keyboard())
        return

    text_result = format_property_search_results(properties=properties, limit=SearchService.DEFAULT_LIMIT)
    applied = format_property_search_applied_filters(filters)
    await message.answer(f"{text_result}\n\n<b>Фильтры:</b>\n{applied}", reply_markup=get_properties_list_inline_keyboard(properties))
    await message.answer("Поиск завершён. Можно запустить новый поиск.", reply_markup=get_search_menu_keyboard())


@router.message(StateFilter(SearchStates))
async def fallback_search_state(message: Message) -> None:
    await message.answer("Используйте кнопки или введите корректное значение.")


async def _save_filter(state: FSMContext, key: str, raw_value: object | None) -> None:
    text = "" if raw_value is None else str(raw_value).strip()
    data = await state.get_data()
    filters = dict(data.get("filters", {}))

    if text and text != SKIP_TEXT:
        filters[key] = raw_value
    elif key in filters:
        filters.pop(key)

    await state.update_data(filters=filters)