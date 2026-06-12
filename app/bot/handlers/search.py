from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.buyer_requests import get_buyer_requests_list_keyboard
from app.bot.keyboards.clients import CANCEL_TEXT, SKIP_TEXT, get_clients_list_inline_keyboard
from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.properties import get_properties_list_inline_keyboard
from app.bot.keyboards.search import (
    ADVANCED_BUYER_SEARCH_TEXT,
    ADVANCED_CLIENT_SEARCH_TEXT,
    ADVANCED_PROPERTY_SEARCH_TEXT,
    QUICK_BUYER_SEARCH_TEXT,
    QUICK_CLIENT_SEARCH_TEXT,
    QUICK_PROPERTY_SEARCH_TEXT,
    SEARCH_MENU_TEXT,
    get_buyer_search_status_keyboard,
    get_client_search_request_type_keyboard,
    get_client_search_status_keyboard,
    get_property_search_status_keyboard,
    get_property_search_type_keyboard,
    get_search_cancel_keyboard,
    get_search_menu_keyboard,
    get_search_skip_cancel_keyboard,
)
from app.bot.states.search_states import SearchStates
from app.common.enums import BuyerRequestStatus, ClientStatus, PropertyStatus, PropertyType, RequestType
from app.common.utils.money import parse_money_range_to_tenge
from app.common.utils.property_search import is_query_too_short, normalize_search_text
from app.common.formatters.search_formatter import (
    format_client_search_applied_filters,
    format_client_search_results,
    format_property_search_applied_filters,
    format_property_search_results,
)
from app.common.formatters.buyer_request_formatter import BUYER_STATUS_LABELS, format_buyers_list
from app.bot.utils.chat_ui import send_clean_bundle, send_clean_screen
from app.services.auth_service import AuthService
from app.services.buyer_requests import BuyerRequestService
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

BUYER_STATUS_MAP: dict[str, BuyerRequestStatus] = {
    label: status
    for status, label in BUYER_STATUS_LABELS.items()
}


async def _show_search_step(
    message: Message,
    state: FSMContext,
    text: str,
    *,
    reply_markup=None,
    parse_mode: str | None = None,
    scope: str = "search_flow",
) -> None:
    await send_clean_screen(
        message,
        state=state,
        scope=scope,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        prefer_edit=False,
    )


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
    await send_clean_screen(message, state=state, scope="search_menu", text="Раздел поиска. Выберите тип поиска:", reply_markup=get_search_menu_keyboard(), prefer_edit=False)


@router.message(F.text == CANCEL_TEXT, StateFilter(SearchStates))
@router.message(Command("cancel"), StateFilter(SearchStates))
async def cancel_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_clean_screen(message, state=state, scope="main_menu", text="Поиск отменён.", reply_markup=get_main_menu_keyboard(), prefer_edit=False)


@router.message(SearchStates.choose_mode, F.text == QUICK_CLIENT_SEARCH_TEXT)
async def choose_quick_client_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="clients")
    await state.set_state(SearchStates.client_quick_query)
    await _show_search_step(
        message,
        state,
        "Введите запрос для клиентов (имя / телефон / район).",
        reply_markup=get_search_cancel_keyboard(),
    )


@router.message(SearchStates.choose_mode, F.text == QUICK_PROPERTY_SEARCH_TEXT)
async def choose_quick_property_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="properties")
    await state.set_state(SearchStates.property_quick_query)
    await _show_search_step(
        message,
        state,
        "Введите запрос для объектов (название / адрес или район / часть номера / цена / площадь / этаж).",
        reply_markup=get_search_cancel_keyboard(),
    )


@router.message(SearchStates.choose_mode, F.text == QUICK_BUYER_SEARCH_TEXT)
async def choose_quick_buyer_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="buyer_requests")
    await state.set_state(SearchStates.buyer_quick_query)
    await _show_search_step(
        message,
        state,
        "Введите запрос для покупателей (имя / телефон / цель / комментарий).",
        reply_markup=get_search_cancel_keyboard(),
    )


@router.message(SearchStates.choose_mode, F.text == ADVANCED_CLIENT_SEARCH_TEXT)
async def choose_advanced_client_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="clients", filters={})
    await state.set_state(SearchStates.client_full_name)
    await _show_search_step(message, state, "Имя клиента (частично) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.choose_mode, F.text == ADVANCED_BUYER_SEARCH_TEXT)
async def choose_advanced_buyer_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="buyer_requests", filters={})
    await state.set_state(SearchStates.buyer_query)
    await _show_search_step(
        message,
        state,
        "Имя, телефон, цель или комментарий покупателя. Можно нажать «Пропустить».",
        reply_markup=get_search_skip_cancel_keyboard(),
    )


@router.message(SearchStates.choose_mode, F.text == ADVANCED_PROPERTY_SEARCH_TEXT)
async def choose_advanced_property_search(message: Message, state: FSMContext) -> None:
    await state.update_data(entity="properties", filters={})
    await state.set_state(SearchStates.property_title)
    await _show_search_step(message, state, "Название объекта (частично) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.client_quick_query)
async def run_quick_client_search(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    search_service: SearchService,
) -> None:
    query = normalize_search_text(message.text)
    if not query:
        await _show_search_step(message, state, "Введите непустой запрос.", reply_markup=get_search_cancel_keyboard())
        return

    if is_query_too_short(query):
        await _show_search_step(message, state, "Введите более точный запрос (минимум 3 буквы или 4 цифры телефона).", reply_markup=get_search_cancel_keyboard())
        return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    filters = {"full_name": query, "district": query, "phone": query, "limit": SearchService.DEFAULT_LIMIT}
    try:
        clients = await search_service.search_clients(current_user=user, filters=filters)
    except ValueError as error:
        await _show_search_step(message, state, str(error), reply_markup=get_search_cancel_keyboard())
        return

    await state.clear()
    if not clients:
        await _show_search_step(message, state, "По вашему запросу клиенты не найдены.", reply_markup=get_search_menu_keyboard())
        return

    applied = format_client_search_applied_filters(filters)
    text = format_client_search_results(clients=clients, limit=SearchService.DEFAULT_LIMIT)
    await send_clean_bundle(
        message,
        state=state,
        items=[
            {
                "scope": "search_results",
                "text": f"{text}\n\nФильтры:\n{applied}",
                "reply_markup": get_clients_list_inline_keyboard(clients),
                "parse_mode": "HTML",
            },
            {
                "scope": "search_menu",
                "text": "Можно открыть карточку клиента по кнопке выше или запустить новый поиск.",
                "reply_markup": get_search_menu_keyboard(),
            },
        ],
    )


@router.message(SearchStates.property_quick_query)
async def run_quick_property_search(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    search_service: SearchService,
) -> None:
    query = normalize_search_text(message.text)
    if not query:
        await _show_search_step(message, state, "Введите непустой запрос.", reply_markup=get_search_cancel_keyboard())
        return

    if is_query_too_short(query):
        await _show_search_step(message, state, "Введите более точный запрос (минимум 3 буквы или 4 цифры телефона).", reply_markup=get_search_cancel_keyboard())
        return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    filters = {"search_text": query, "limit": SearchService.DEFAULT_LIMIT}
    try:
        properties = await search_service.search_properties(current_user=user, filters=filters)
    except ValueError as error:
        await _show_search_step(message, state, str(error), reply_markup=get_search_cancel_keyboard())
        return

    await state.clear()
    if not properties:
        await _show_search_step(
            message,
            state,
            f"По запросу «{query}» ничего не найдено.\n\n"
            "Попробуйте:\n"
            "• название или адрес: Абай, Самал, Каратал\n"
            "• часть номера: 7775\n"
            "• площадь: 58.6\n"
            "• цена: 19.5\n"
            "• этаж: 2/5",
            reply_markup=get_search_menu_keyboard(),
        )
        return

    applied = format_property_search_applied_filters(filters)
    text = format_property_search_results(properties=properties, limit=SearchService.DEFAULT_LIMIT)
    await send_clean_bundle(
        message,
        state=state,
        items=[
            {
                "scope": "search_results",
                "text": f"{text}\n\nФильтры:\n{applied}",
                "reply_markup": get_properties_list_inline_keyboard(properties),
                "parse_mode": "HTML",
            },
            {
                "scope": "search_menu",
                "text": "Можно открыть карточку объекта по кнопке выше или запустить новый поиск.",
                "reply_markup": get_search_menu_keyboard(),
            },
        ],
    )


@router.message(SearchStates.buyer_quick_query)
async def run_quick_buyer_search(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    buyer_request_service: BuyerRequestService,
) -> None:
    query = normalize_search_text(message.text)
    if not query:
        await _show_search_step(message, state, "Введите непустой запрос.", reply_markup=get_search_cancel_keyboard())
        return

    if is_query_too_short(query):
        await _show_search_step(message, state, "Введите более точный запрос (минимум 3 буквы или 4 цифры телефона).", reply_markup=get_search_cancel_keyboard())
        return

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    requests = await buyer_request_service.search_requests(
        current_user=user,
        query=query,
        limit=SearchService.DEFAULT_LIMIT,
    )

    await state.clear()
    if not requests:
        await _show_search_step(message, state, "По вашему запросу покупатели не найдены.", reply_markup=get_search_menu_keyboard())
        return

    text = format_buyers_list(
        requests,
        total_count=len(requests),
        page=1,
        total_pages=1,
    )
    await send_clean_bundle(
        message,
        state=state,
        items=[
            {
                "scope": "search_results",
                "text": text,
                "reply_markup": get_buyer_requests_list_keyboard(requests=requests, page=1, total_pages=1),
                "parse_mode": "HTML",
            },
            {
                "scope": "search_menu",
                "text": "Можно открыть карточку покупателя по кнопке выше или запустить новый поиск.",
                "reply_markup": get_search_menu_keyboard(),
            },
        ],
    )


@router.message(SearchStates.buyer_query)
async def buyer_filter_query(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "query", message.text)
    await state.set_state(SearchStates.buyer_status)
    await _show_search_step(
        message,
        state,
        "Статус покупателя или «Пропустить»:",
        reply_markup=get_buyer_search_status_keyboard(),
    )


@router.message(SearchStates.buyer_status)
async def buyer_filter_status(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    buyer_request_service: BuyerRequestService,
) -> None:
    text = (message.text or "").strip()
    if text != SKIP_TEXT:
        status = BUYER_STATUS_MAP.get(text)
        if status is None:
            await _show_search_step(
                message,
                state,
                "Выберите статус кнопкой или нажмите «Пропустить».",
                reply_markup=get_buyer_search_status_keyboard(),
            )
            return
        await _save_filter(state, "status", status)

    user = await _get_current_user(message, auth_service)
    if user is None:
        await state.clear()
        return

    data = await state.get_data()
    filters = dict(data.get("filters", {}))
    query = str(filters.get("query") or "").strip()
    status_filter = filters.get("status")
    if not query and status_filter is None:
        await _show_search_step(
            message,
            state,
            "Укажите минимум один параметр для поиска покупателей.",
            reply_markup=get_search_menu_keyboard(),
        )
        await state.set_state(SearchStates.choose_mode)
        return

    requests = await buyer_request_service.search_requests(
        current_user=user,
        query=query,
        status=status_filter if isinstance(status_filter, BuyerRequestStatus) else None,
        limit=SearchService.DEFAULT_LIMIT,
    )

    await state.clear()
    if not requests:
        await _show_search_step(message, state, "По выбранным фильтрам покупатели не найдены.", reply_markup=get_search_menu_keyboard())
        return

    text_result = format_buyers_list(
        requests,
        total_count=len(requests),
        page=1,
        total_pages=1,
    )
    await send_clean_bundle(
        message,
        state=state,
        items=[
            {
                "scope": "search_results",
                "text": text_result,
                "reply_markup": get_buyer_requests_list_keyboard(requests=requests, page=1, total_pages=1),
                "parse_mode": "HTML",
            },
            {
                "scope": "search_menu",
                "text": "Поиск завершён. Можно открыть карточку покупателя или запустить новый поиск.",
                "reply_markup": get_search_menu_keyboard(),
            },
        ],
    )


@router.message(SearchStates.client_full_name)
async def client_filter_full_name(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "full_name", message.text)
    await state.set_state(SearchStates.client_phone)
    await _show_search_step(message, state, "Телефон (полный или часть) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.client_phone)
async def client_filter_phone(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "phone", message.text)
    await state.set_state(SearchStates.client_district)
    await _show_search_step(message, state, "Район (полный или часть) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.client_district)
async def client_filter_district(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "district", message.text)
    await state.set_state(SearchStates.client_status)
    await _show_search_step(message, state, "Статус клиента или «Пропустить»:", reply_markup=get_client_search_status_keyboard())


@router.message(SearchStates.client_status)
async def client_filter_status(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == SKIP_TEXT:
        await state.set_state(SearchStates.client_request_type)
        await _show_search_step(message, state, "Тип запроса или «Пропустить»:", reply_markup=get_client_search_request_type_keyboard())
        return

    status = CLIENT_STATUS_MAP.get(text)
    if status is None:
        await _show_search_step(message, state, "Выберите статус кнопкой или нажмите «Пропустить».", reply_markup=get_client_search_status_keyboard())
        return

    await _save_filter(state, "status", status)
    await state.set_state(SearchStates.client_request_type)
    await _show_search_step(message, state, "Тип запроса или «Пропустить»:", reply_markup=get_client_search_request_type_keyboard())


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
            await _show_search_step(
                message,
                state,
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
        await _show_search_step(message, state, str(error), reply_markup=get_search_menu_keyboard())
        await state.set_state(SearchStates.choose_mode)
        return

    await state.clear()
    if not clients:
        await _show_search_step(message, state, "По выбранным фильтрам клиенты не найдены.", reply_markup=get_search_menu_keyboard())
        return

    text_result = format_client_search_results(clients=clients, limit=SearchService.DEFAULT_LIMIT)
    applied = format_client_search_applied_filters(filters)
    await send_clean_bundle(
        message,
        state=state,
        items=[
            {
                "scope": "search_results",
                "text": f"{text_result}\n\nФильтры:\n{applied}",
                "reply_markup": get_clients_list_inline_keyboard(clients),
                "parse_mode": "HTML",
            },
            {
                "scope": "search_menu",
                "text": "Поиск завершён. Можно запустить новый поиск.",
                "reply_markup": get_search_menu_keyboard(),
            },
        ],
    )


@router.message(SearchStates.property_title)
async def property_filter_title(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "title", message.text)
    await state.set_state(SearchStates.property_district)
    await _show_search_step(message, state, "Район (полный или часть) или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.property_district)
async def property_filter_district(message: Message, state: FSMContext) -> None:
    await _save_filter(state, "district", message.text)
    await state.set_state(SearchStates.property_type)
    await _show_search_step(message, state, "Тип недвижимости или «Пропустить»:", reply_markup=get_property_search_type_keyboard())


@router.message(SearchStates.property_type)
async def property_filter_type(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == SKIP_TEXT:
        await state.set_state(SearchStates.property_status)
        await _show_search_step(message, state, "Статус объекта или «Пропустить»:", reply_markup=get_property_search_status_keyboard())
        return

    property_type = PROPERTY_TYPE_MAP.get(text)
    if property_type is None:
        await _show_search_step(message, state, "Выберите тип кнопкой или «Пропустить».", reply_markup=get_property_search_type_keyboard())
        return

    await _save_filter(state, "property_type", property_type)
    await state.set_state(SearchStates.property_status)
    await _show_search_step(message, state, "Статус объекта или «Пропустить»:", reply_markup=get_property_search_status_keyboard())


@router.message(SearchStates.property_status)
async def property_filter_status(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == SKIP_TEXT:
        await state.set_state(SearchStates.property_price_min)
        await _show_search_step(message, state, "Минимальная цена или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())
        return

    status = PROPERTY_STATUS_MAP.get(text)
    if status is None:
        await _show_search_step(message, state, "Выберите статус кнопкой или «Пропустить».", reply_markup=get_property_search_status_keyboard())
        return

    await _save_filter(state, "status", status)
    await state.set_state(SearchStates.property_price_min)
    await _show_search_step(message, state, "Минимальная цена или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.property_price_min)
async def property_filter_price_min(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text != SKIP_TEXT:
        value_min, value_max = parse_money_range_to_tenge(text)
        if value_min is None and value_max is None:
            await _show_search_step(message, state, "Введите цену, например 19.5, от 20, до 25 или 15-25.", reply_markup=get_search_skip_cancel_keyboard())
            return

        if value_min is not None:
            await _save_filter(state, "price_min", value_min)
        if value_max is not None:
            await _save_filter(state, "price_max", value_max)

        if value_max is not None:
            await state.set_state(SearchStates.property_rooms)
            await _show_search_step(message, state, "Количество комнат или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())
            return

    await state.set_state(SearchStates.property_price_max)
    await _show_search_step(message, state, "Максимальная цена или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


@router.message(SearchStates.property_price_max)
async def property_filter_price_max(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text != SKIP_TEXT:
        _, value_max = parse_money_range_to_tenge(f"до {text}" if "до" not in text.lower() else text)
        if value_max is None:
            await _show_search_step(message, state, "Введите цену, например 25 или 19.5 млн, либо «Пропустить».", reply_markup=get_search_skip_cancel_keyboard())
            return
        await _save_filter(state, "price_max", value_max)

    await state.set_state(SearchStates.property_rooms)
    await _show_search_step(message, state, "Количество комнат или «Пропустить»:", reply_markup=get_search_skip_cancel_keyboard())


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
            await _show_search_step(message, state, "Введите целое число больше 0, «Студия» или «Пропустить».", reply_markup=get_search_skip_cancel_keyboard())
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
        await _show_search_step(message, state, str(error), reply_markup=get_search_menu_keyboard())
        await state.set_state(SearchStates.choose_mode)
        return

    await state.clear()
    if not properties:
        await _show_search_step(message, state, "По выбранным фильтрам объекты не найдены.", reply_markup=get_search_menu_keyboard())
        return

    text_result = format_property_search_results(properties=properties, limit=SearchService.DEFAULT_LIMIT)
    applied = format_property_search_applied_filters(filters)
    await send_clean_bundle(
        message,
        state=state,
        items=[
            {
                "scope": "search_results",
                "text": f"{text_result}\n\n<b>Фильтры:</b>\n{applied}",
                "reply_markup": get_properties_list_inline_keyboard(properties),
                "parse_mode": "HTML",
            },
            {
                "scope": "search_menu",
                "text": "Поиск завершён. Можно запустить новый поиск.",
                "reply_markup": get_search_menu_keyboard(),
            },
        ],
    )


@router.message(StateFilter(SearchStates))
async def fallback_search_state(message: Message, state: FSMContext) -> None:
    await _show_search_step(message, state, "Используйте кнопки или введите корректное значение.")


async def _save_filter(state: FSMContext, key: str, raw_value: object | None) -> None:
    text = "" if raw_value is None else str(raw_value).strip()
    data = await state.get_data()
    filters = dict(data.get("filters", {}))

    if text and text != SKIP_TEXT:
        filters[key] = raw_value
    elif key in filters:
        filters.pop(key)

    await state.update_data(filters=filters)
