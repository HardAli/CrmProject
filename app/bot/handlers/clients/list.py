from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.clients import (
    BUY_CLIENTS_BY_STATUS_TEXT,
    BUY_CLIENTS_TEXT,
    CLIENTS_MENU_TEXT,
    RECENT_CLIENTS_TEXT,
    SELL_CLIENTS_BY_STATUS_TEXT,
    SELL_CLIENTS_TEXT,
    build_budget_filter_keyboard,
    build_client_filters_menu_keyboard,
    build_clients_list_keyboard,
    build_contact_filter_keyboard,
    build_deal_filter_keyboard,
    build_district_filter_keyboard,
    build_quick_filters_keyboard,
    build_rooms_filter_keyboard,
    build_sort_keyboard,
    build_status_filter_keyboard,
    build_task_filter_keyboard,
    get_clients_menu_keyboard,
    get_status_filter_keyboard,
)
from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.states.clients import ClientListStates
from app.common.client_filters import ACTIVE_CLIENT_STATUSES, get_default_client_filters, normalize_filters
from app.common.enums import ClientStatus, RequestType
from app.common.formatters.client_formatter import (
    STATUS_LABELS,
    build_client_filters_menu_text,
    build_clients_list_text,
    format_clients_list,
)
from app.bot.utils.chat_ui import send_clean_screen
from app.services.auth_service import AuthService
from app.services.clients import ClientService

router = Router(name="client_list")
PER_PAGE = 5
FILTERS_KEY = "client_list_filters"


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


async def _get_callback_user(callback: CallbackQuery, auth_service: AuthService):
    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return None
    return user


async def _load_filters(state: FSMContext) -> dict:
    raw = await state.get_data()
    return normalize_filters(raw.get(FILTERS_KEY))


async def _save_filters(state: FSMContext, filters: dict) -> None:
    await state.update_data({FILTERS_KEY: normalize_filters(filters)})


async def _render_clients_list(
    target: Message | CallbackQuery,
    state: FSMContext,
    client_service: ClientService,
    user,
    filters: dict,
) -> None:
    clients, total_count, total_pages = await client_service.get_clients_filtered(
        current_user=user,
        filters=filters,
        per_page=PER_PAGE,
    )
    safe_page = min(filters.get("page", 1), total_pages)
    if safe_page != filters.get("page", 1):
        filters["page"] = safe_page
        clients, total_count, total_pages = await client_service.get_clients_filtered(
            current_user=user,
            filters=filters,
            per_page=PER_PAGE,
        )

    text = build_clients_list_text(
        clients=clients,
        filters=filters,
        total_count=total_count,
        page=filters["page"],
        per_page=PER_PAGE,
    )
    await send_clean_screen(
        target,
        state=state,
        scope="clients_list",
        text=text,
        reply_markup=build_clients_list_keyboard(clients=clients, filters=filters, page=filters["page"], total_pages=total_pages),
        prefer_edit=isinstance(target, CallbackQuery),
    )


async def _render_filters_menu(target: Message | CallbackQuery, state: FSMContext, filters: dict) -> None:
    await send_clean_screen(
        target,
        state=state,
        scope="clients_filters",
        text=build_client_filters_menu_text(filters),
        reply_markup=build_client_filters_menu_keyboard(),
        parse_mode="HTML",
        prefer_edit=isinstance(target, CallbackQuery),
    )


@router.message(F.text == CLIENTS_MENU_TEXT)
async def open_clients_menu(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await send_clean_screen(message, state=state, scope="clients_menu", text="Раздел клиентов. Выберите действие:", reply_markup=get_clients_menu_keyboard(), prefer_edit=False)


@router.message(F.text == "⬅️ Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext) -> None:
    await send_clean_screen(message, state=state, scope="main_menu", text="Главное меню:", reply_markup=get_main_menu_keyboard(), prefer_edit=False)


async def _show_clients_by_deal(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
    request_type: RequestType,
) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    filters = get_default_client_filters()
    filters["deal_types"] = [request_type.value]
    await _save_filters(state, filters)
    await _render_clients_list(target=message, state=state, client_service=client_service, user=user, filters=filters)


@router.message(StateFilter(None), F.text == BUY_CLIENTS_TEXT)
async def show_buy_clients(message: Message, state: FSMContext, auth_service: AuthService, client_service: ClientService) -> None:
    await _show_clients_by_deal(message, state, auth_service, client_service, RequestType.BUY)


@router.message(StateFilter(None), F.text == SELL_CLIENTS_TEXT)
async def show_sell_clients(message: Message, state: FSMContext, auth_service: AuthService, client_service: ClientService) -> None:
    await _show_clients_by_deal(message, state, auth_service, client_service, RequestType.SELL)


@router.callback_query(F.data == "clients_list_open")
async def open_clients_list_callback(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    user = await _get_callback_user(callback, auth_service)
    if user is None:
        return
    filters = await _load_filters(state)
    await _save_filters(state, filters)
    await _render_clients_list(target=callback, state=state, client_service=client_service, user=user, filters=filters)
    await callback.answer()


@router.callback_query(F.data == "clients_filters_open")
async def open_filters_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _load_filters(state)
    await _render_filters_menu(target=callback, state=state, filters=filters)
    await callback.answer()


@router.callback_query(F.data == "clients_filters_reset")
async def reset_filters(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    user = await _get_callback_user(callback, auth_service)
    if user is None:
        return
    filters = get_default_client_filters()
    await _save_filters(state, filters)
    await _render_clients_list(callback, state, client_service, user, filters)
    await callback.answer("Фильтры сброшены")


@router.callback_query(F.data == "clients_filters_status")
async def open_status_filter(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _load_filters(state)
    selected = set(filters.get("statuses") or [])
    labels = [STATUS_LABELS[ClientStatus(v)] for v in selected if v in {s.value for s in ClientStatus}]
    selected_text = ", ".join(labels) if labels else "—"
    await send_clean_screen(
        callback,
        state=state,
        scope="clients_filter_status",
        text=f"Статус клиента\n\nВыбрано: {selected_text}",
        reply_markup=build_status_filter_keyboard(selected),
        prefer_edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_filter_status_toggle:"))
async def toggle_status_filter(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    status_value = callback.data.split(":", maxsplit=1)[1]
    filters = await _load_filters(state)
    selected = set(filters.get("statuses") or [])
    if status_value in selected:
        selected.remove(status_value)
    else:
        selected.add(status_value)
    filters["statuses"] = list(selected)
    filters["page"] = 1
    await _save_filters(state, filters)
    await callback.message.edit_reply_markup(reply_markup=build_status_filter_keyboard(selected))
    await callback.answer()


@router.callback_query(F.data == "clients_filter_status_active")
async def set_active_statuses(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    filters["statuses"] = [status.value for status in ACTIVE_CLIENT_STATUSES]
    filters["page"] = 1
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_status_filter_keyboard(set(filters["statuses"])))
    await callback.answer("Активные статусы выбраны")


@router.callback_query(F.data == "clients_filter_status_all")
async def set_all_statuses(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    filters["statuses"] = [status.value for status in ClientStatus]
    filters["page"] = 1
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_status_filter_keyboard(set(filters["statuses"])))
    await callback.answer("Показываем все статусы")


@router.callback_query(F.data == "clients_filters_deal")
async def open_deal_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_filter_deal",
            text="Тип сделки",
            reply_markup=build_deal_filter_keyboard(set(filters.get("deal_types") or [])),
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_filter_deal_toggle:"))
async def toggle_deal_filter(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", maxsplit=1)[1]
    filters = await _load_filters(state)
    selected = set(filters.get("deal_types") or [])
    if value in selected:
        selected.remove(value)
    else:
        selected.add(value)
    filters["deal_types"] = list(selected)
    filters["page"] = 1
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_deal_filter_keyboard(selected))
    await callback.answer()


@router.callback_query(F.data == "clients_filter_deal_any")
async def clear_deal_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    filters["deal_types"] = []
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_deal_filter_keyboard(set()))
    await callback.answer("Сделка: любая")


@router.callback_query(F.data == "clients_filters_rooms")
async def open_rooms_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_filter_rooms",
            text="Комнатность",
            reply_markup=build_rooms_filter_keyboard(set(filters.get("rooms") or [])),
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_filter_rooms_toggle:"))
async def toggle_rooms_filter(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", maxsplit=1)[1]
    filters = await _load_filters(state)
    selected = set(filters.get("rooms") or [])
    if value in selected:
        selected.remove(value)
    else:
        selected.add(value)
    filters["rooms"] = list(selected)
    filters["page"] = 1
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_rooms_filter_keyboard(selected))
    await callback.answer()


@router.callback_query(F.data == "clients_filter_rooms_any")
async def clear_rooms_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    filters["rooms"] = []
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_rooms_filter_keyboard(set()))
    await callback.answer("Комнатность: любая")


@router.callback_query(F.data == "clients_filters_budget")
async def open_budget_filter(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_filter_budget",
            text="Бюджет",
            reply_markup=build_budget_filter_keyboard(),
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_filter_budget_max:"))
async def set_budget_max(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":", maxsplit=1)[1])
    filters = await _load_filters(state)
    filters["budget_min"] = None
    filters["budget_max"] = value
    filters["page"] = 1
    await _save_filters(state, filters)
    await callback.answer("Бюджет обновлён")


@router.callback_query(F.data.startswith("clients_filter_budget_min:"))
async def set_budget_min(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":", maxsplit=1)[1])
    filters = await _load_filters(state)
    filters["budget_min"] = value
    filters["budget_max"] = None
    filters["page"] = 1
    await _save_filters(state, filters)
    await callback.answer("Бюджет обновлён")


@router.callback_query(F.data == "clients_filter_budget_any")
async def clear_budget_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    filters["budget_min"] = None
    filters["budget_max"] = None
    await _save_filters(state, filters)
    await callback.answer("Бюджет: любой")


@router.callback_query(F.data == "clients_filters_district")
async def open_district_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_filter_district",
            text="<b>Район</b>",
            reply_markup=build_district_filter_keyboard(set(filters.get("districts") or [])),
            parse_mode="HTML",
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_filter_district_toggle:"))
async def toggle_district_filter(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", maxsplit=1)[1]
    filters = await _load_filters(state)
    selected = set(filters.get("districts") or [])
    if value in selected:
        selected.remove(value)
    else:
        selected.add(value)
    filters["districts"] = list(selected)
    filters["page"] = 1
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_district_filter_keyboard(selected))
    await callback.answer()


@router.callback_query(F.data == "clients_filter_district_any")
async def clear_district_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _load_filters(state)
    filters["districts"] = []
    await _save_filters(state, filters)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=build_district_filter_keyboard(set()))
    await callback.answer("Район: любой")


@router.callback_query(F.data == "clients_filters_contact")
async def open_contact_filter(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_filter_contact",
            text="<b>Следующий контакт</b>",
            reply_markup=build_contact_filter_keyboard(),
            parse_mode="HTML",
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_filter_contact:"))
async def set_contact_filter(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", maxsplit=1)[1]
    filters = await _load_filters(state)
    filters["next_contact_mode"] = None if value == "any" else value
    filters["page"] = 1
    await _save_filters(state, filters)
    await callback.answer("Контактный фильтр обновлён")


@router.callback_query(F.data == "clients_filters_tasks")
async def open_tasks_filter(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_filter_tasks",
            text="<b>Задачи</b>",
            reply_markup=build_task_filter_keyboard(),
            parse_mode="HTML",
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.in_({"clients_filters_source", "clients_filters_objects", "clients_filters_extra"}))
async def show_not_ready_filter(callback: CallbackQuery) -> None:
    await callback.answer("Раздел будет расширен на следующем этапе", show_alert=False)


@router.callback_query(F.data.startswith("clients_filter_tasks:"))
async def set_tasks_filter(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", maxsplit=1)[1]
    filters = await _load_filters(state)
    filters["task_mode"] = None if value == "any" else value
    filters["page"] = 1
    await _save_filters(state, filters)
    await callback.answer("Фильтр задач обновлён")


@router.callback_query(F.data == "clients_quick_open")
async def open_quick_filters(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_quick_filters",
            text="<b>Быстрые фильтры</b>",
            reply_markup=build_quick_filters_keyboard(),
            parse_mode="HTML",
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_quick:"))
async def apply_quick_filter(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", maxsplit=1)[1]
    filters = get_default_client_filters()
    quick_name = "быстрый"

    if key == "today_contact":
        filters["next_contact_mode"] = "today"
        quick_name = "сегодня связаться"
    elif key == "overdue_contact":
        filters["next_contact_mode"] = "overdue"
        quick_name = "просроченные контакты"
    elif key == "hot":
        filters["statuses"] = [ClientStatus.WAITING.value]
        quick_name = "горячие клиенты"
    elif key == "new":
        filters["statuses"] = [ClientStatus.NEW.value]
        quick_name = "новые клиенты"
    elif key == "waiting_selection":
        filters["object_mode"] = "waiting_selection"
        quick_name = "ждут подборку"
    elif key == "no_next_contact":
        filters["next_contact_mode"] = "none"
        quick_name = "без след. контакта"
    elif key == "no_tasks":
        filters["task_mode"] = "none"
        quick_name = "без задач"
    elif key == "failed":
        filters["statuses"] = [ClientStatus.CLOSED_FAILED.value]
        quick_name = "отказы"
    elif key == "closed":
        filters["statuses"] = [ClientStatus.CLOSED_SUCCESS.value]
        quick_name = "закрытые"

    filters["quick_filter"] = quick_name
    await _save_filters(state, filters)
    await callback.answer(f"Выбран фильтр: {quick_name}")


@router.callback_query(F.data == "clients_sort_open")
async def open_sort_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_sort",
            text="<b>Сортировка</b>",
            reply_markup=build_sort_keyboard(),
            parse_mode="HTML",
            prefer_edit=True,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("clients_sort:"))
async def set_sort_mode(callback: CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split(":", maxsplit=1)[1]
    filters = await _load_filters(state)
    filters["sort"] = mode
    filters["page"] = 1
    await _save_filters(state, filters)
    await callback.answer("Сортировка применена")


@router.callback_query(F.data == "clients_page_prev")
async def page_prev(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    filters = await _load_filters(state)
    filters["page"] = max(1, int(filters.get("page", 1)) - 1)
    await _save_filters(state, filters)
    if callback.message is not None:
        user = await _get_callback_user(callback, auth_service)
        if user is not None:
            await _render_clients_list(callback, state, client_service, user, filters)
    await callback.answer()


@router.callback_query(F.data == "clients_page_next")
async def page_next(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    filters = await _load_filters(state)
    filters["page"] = int(filters.get("page", 1)) + 1
    await _save_filters(state, filters)
    if callback.message is not None:
        user = await _get_callback_user(callback, auth_service)
        if user is not None:
            await _render_clients_list(callback, state, client_service, user, filters)
    await callback.answer()


@router.callback_query(F.data == "clients_search_open")
async def open_search_input(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ClientListStates.search_query)
    if callback.message:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_search_prompt",
            text="Введите строку поиска по клиентам (имя/телефон/район/статус/источник/заметка).",
            prefer_edit=True,
        )


@router.message(ClientListStates.search_query)
async def apply_search_query(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    filters = await _load_filters(state)
    filters["search_query"] = query or None

    lowered = query.lower()
    if "сегодня" in lowered:
        filters["next_contact_mode"] = "today"
    if "без задач" in lowered:
        filters["task_mode"] = "none"
    if "горяч" in lowered:
        filters["statuses"] = [ClientStatus.WAITING.value]

    await _save_filters(state, filters)
    await state.clear()
    await send_clean_screen(
        message,
        state=state,
        scope="clients_search_saved",
        text="Поиск сохранён. Нажмите «Купить», «Продать» или «✅ Показать клиентов».",
        prefer_edit=False,
    )


async def _show_status_filter_for_deal(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    request_type: RequestType,
) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    title = "покупателей" if request_type == RequestType.BUY else "продавцов"
    await send_clean_screen(
        message,
        state=state,
        scope="clients_status_filter",
        text=f"Выберите статус {title}:",
        reply_markup=get_status_filter_keyboard(request_type.value),
        prefer_edit=False,
    )


@router.message(StateFilter(None), F.text == BUY_CLIENTS_BY_STATUS_TEXT)
async def show_buy_status_filter(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    await _show_status_filter_for_deal(message, state, auth_service, RequestType.BUY)


@router.message(StateFilter(None), F.text == SELL_CLIENTS_BY_STATUS_TEXT)
async def show_sell_status_filter(message: Message, state: FSMContext, auth_service: AuthService) -> None:
    await _show_status_filter_for_deal(message, state, auth_service, RequestType.SELL)


@router.callback_query(F.data.startswith("client_status:"))
async def show_clients_by_status(
    callback: CallbackQuery,
    state: FSMContext,
    auth_service: AuthService,
    client_service: ClientService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    raw_deal_type: str | None = None
    raw_status = ""
    if len(parts) == 2:
        _, raw_status = parts
    elif len(parts) == 3:
        _, raw_deal_type, raw_status = parts
    else:
        await callback.answer("Неизвестная команда", show_alert=True)
        return

    try:
        status = ClientStatus(raw_status)
    except ValueError:
        await callback.answer("Неизвестный статус", show_alert=True)
        return
    try:
        request_type = RequestType(raw_deal_type) if raw_deal_type else None
    except ValueError:
        await callback.answer("Неизвестный тип клиента", show_alert=True)
        return

    if request_type is not None:
        filters = get_default_client_filters()
        filters["statuses"] = [status.value]
        filters["deal_types"] = [request_type.value]
        await _save_filters(state, filters)
        await _render_clients_list(callback, state, client_service, user, filters)
        await callback.answer()
        return

    clients = list(
        await client_service.get_clients_by_status(
            current_user=user,
            status=status,
            limit=10,
        )
    )
    title = f"Клиенты со статусом: {STATUS_LABELS.get(status, status.value)}"

    if not clients:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_by_status",
            text="По выбранному статусу клиентов пока нет.",
            prefer_edit=True,
        )
    else:
        await send_clean_screen(
            callback,
            state=state,
            scope="clients_by_status",
            text=format_clients_list(clients=clients, title=title, limit=10),
            parse_mode="HTML",
            prefer_edit=True,
        )

    await callback.answer()


@router.message(F.text == RECENT_CLIENTS_TEXT)
async def show_recent_clients(message: Message, state: FSMContext, auth_service: AuthService, client_service: ClientService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    clients = list(await client_service.get_recent_clients(current_user=user, limit=10))
    if not clients:
        await send_clean_screen(message, state=state, scope="recent_clients", text="У вас пока нет клиентов.", prefer_edit=False)
        return
    await send_clean_screen(
        message,
        state=state,
        scope="recent_clients",
        text=format_clients_list(clients=clients, title="Последние добавленные", limit=10),
        parse_mode="HTML",
        prefer_edit=False,
    )
