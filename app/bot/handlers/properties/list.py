from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.object_filters import (
    OBJ_FILTER_PREFIX,
    build_area_filter_keyboard,
    build_date_filter_keyboard,
    build_district_filter_keyboard,
    build_filters_menu_keyboard,
    build_floor_filter_keyboard,
    build_objects_list_keyboard,
    build_price_filter_keyboard,
    build_rooms_filter_keyboard,
    build_sort_keyboard,
    build_status_filter_keyboard,
    build_type_filter_keyboard,
)
from app.bot.keyboards.properties import (
    BACK_TO_MAIN_MENU_TEXT,
    GLOBAL_PROPERTIES_TEXT,
    MY_PROPERTIES_TEXT,
    PROPERTIES_MENU_TEXT,
    RECENT_PROPERTIES_TEXT,
    get_properties_list_inline_keyboard,
    get_properties_menu_keyboard,
)
from app.common.enums import UserRole
from app.common.formatters.object_filters_formatter import (
    build_filters_menu_text,
    build_objects_list_text,
)
from app.common.formatters.property_formatter import format_properties_list
from app.services.auth_service import AuthService
from app.services.object_filters import (
    AREA_PRESETS,
    get_default_object_filters,
    reset_object_filters,
    update_object_filter,
)
from app.services.properties import PropertyService

router = Router(name="property_list")
DEFAULT_LIST_LIMIT = 10
OBJECT_FILTERS_KEY = "object_filters"
GLOBAL_PER_PAGE = 5


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


async def _show_properties(message: Message, properties: list, title: str, limit: int) -> None:
    if not properties:
        await message.answer("Объекты не найдены.")
        return

    await message.answer(
        format_properties_list(properties=properties, title=title, limit=limit),
        reply_markup=get_properties_list_inline_keyboard(properties),
    )


async def _get_filters(state: FSMContext) -> dict[str, object]:
    data = await state.get_data()
    filters = data.get(OBJECT_FILTERS_KEY)
    if isinstance(filters, dict):
        return filters
    filters = get_default_object_filters()
    await state.update_data(**{OBJECT_FILTERS_KEY: filters})
    return filters


async def _save_filters(state: FSMContext, filters: dict[str, object]) -> None:
    await state.update_data(**{OBJECT_FILTERS_KEY: filters})


async def _render_global_objects(
    target: Message | CallbackQuery,
    *,
    current_user,
    state: FSMContext,
    property_service: PropertyService,
    edit: bool,
) -> None:
    filters = await _get_filters(state)
    page = int(filters.get("page", 1) or 1)

    objects, total_count, total_pages = await property_service.get_filtered_global_properties(
        current_user=current_user,
        filters=filters,
        per_page=GLOBAL_PER_PAGE,
    )
    if page > total_pages:
        filters = update_object_filter(filters, "page", total_pages, reset_page=False)
        await _save_filters(state, filters)
        page = total_pages
        objects, total_count, total_pages = await property_service.get_filtered_global_properties(
            current_user=current_user,
            filters=filters,
            per_page=GLOBAL_PER_PAGE,
        )

    text = build_objects_list_text(
        objects=list(objects),
        filters=filters,
        total_count=total_count,
        page=page,
        per_page=GLOBAL_PER_PAGE,
    )
    keyboard = build_objects_list_keyboard(list(objects), filters, page, total_pages)

    if isinstance(target, CallbackQuery):
        if target.message is None:
            return
        if edit:
            await target.message.edit_text(text, reply_markup=keyboard)
        else:
            await target.message.answer(text, reply_markup=keyboard)
        await target.answer()
    else:
        await target.answer(text, reply_markup=keyboard)


@router.message(F.text == PROPERTIES_MENU_TEXT)
async def open_properties_menu(message: Message, auth_service: AuthService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    await message.answer("Раздел объектов. Выберите действие:", reply_markup=get_properties_menu_keyboard())


@router.message(F.text.in_({BACK_TO_MAIN_MENU_TEXT, "⬅️ Главное меню"}))
async def back_to_main_menu(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())


@router.message(F.text == MY_PROPERTIES_TEXT)
async def show_my_properties(message: Message, auth_service: AuthService, property_service: PropertyService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    properties = list(await property_service.get_my_properties(current_user=user, limit=DEFAULT_LIST_LIMIT))
    title = "Мои объекты" if user.role == UserRole.MANAGER else "Все объекты"
    await _show_properties(message, properties, title=title, limit=DEFAULT_LIST_LIMIT)


@router.message(F.text == RECENT_PROPERTIES_TEXT)
async def show_recent_properties(message: Message, auth_service: AuthService, property_service: PropertyService) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    properties = list(await property_service.get_recent_properties(current_user=user, limit=DEFAULT_LIST_LIMIT))
    await _show_properties(message, properties, title="Последние добавленные объекты", limit=DEFAULT_LIST_LIMIT)


@router.message(F.text == GLOBAL_PROPERTIES_TEXT)
async def show_global_properties(
    message: Message,
    auth_service: AuthService,
    property_service: PropertyService,
    state: FSMContext,
) -> None:
    user = await _get_current_user(message, auth_service)
    if user is None:
        return

    filters = await _get_filters(state)
    filters = update_object_filter(filters, "page", 1, reset_page=False)
    await _save_filters(state, filters)
    await _render_global_objects(message, current_user=user, state=state, property_service=property_service, edit=False)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:search")
async def search_stub(callback: CallbackQuery) -> None:
    await callback.answer("Поиск в разделе будет добавлен отдельно.", show_alert=False)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:menu")
async def open_filters_menu(
    callback: CallbackQuery,
    auth_service: AuthService,
    property_service: PropertyService,
    state: FSMContext,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    filters = await _get_filters(state)
    available_fields = await property_service.get_available_object_filter_fields()
    text = build_filters_menu_text(filters, available_fields=available_fields)
    keyboard = build_filters_menu_keyboard(filters, available_fields=available_fields)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:show")
async def show_filtered_objects(
    callback: CallbackQuery,
    auth_service: AuthService,
    property_service: PropertyService,
    state: FSMContext,
) -> None:
    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await _render_global_objects(callback, current_user=user, state=state, property_service=property_service, edit=True)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:reset")
async def reset_filters(
    callback: CallbackQuery,
    auth_service: AuthService,
    property_service: PropertyService,
    state: FSMContext,
) -> None:
    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await _save_filters(state, reset_object_filters())
    await _render_global_objects(callback, current_user=user, state=state, property_service=property_service, edit=True)


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:page:"))
async def paginate_objects(
    callback: CallbackQuery,
    auth_service: AuthService,
    property_service: PropertyService,
    state: FSMContext,
) -> None:
    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    page_raw = callback.data.split(":")[-1]
    if not page_raw.isdigit():
        await callback.answer("Некорректная страница", show_alert=True)
        return

    filters = await _get_filters(state)
    filters = update_object_filter(filters, "page", max(1, int(page_raw)), reset_page=False)
    await _save_filters(state, filters)
    await _render_global_objects(callback, current_user=user, state=state, property_service=property_service, edit=True)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:rooms")
async def open_rooms_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    selected = ", ".join(str(v) for v in filters.get("rooms", [])) or "нет"
    await callback.message.edit_text("<b>Комнатность</b>\n\nВыбрано: " + selected, reply_markup=build_rooms_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:room:"))
async def toggle_room(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    room_value = callback.data.split(":")[-1]
    filters = await _get_filters(state)
    rooms = {str(v) for v in filters.get("rooms", [])}
    if room_value in rooms:
        rooms.remove(room_value)
    else:
        rooms.add(room_value)
    filters = update_object_filter(filters, "rooms", sorted(rooms))
    await _save_filters(state, filters)
    selected = ", ".join(str(v) for v in filters.get("rooms", [])) or "нет"
    await callback.message.edit_text("<b>Комнатность</b>\n\nВыбрано: " + selected, reply_markup=build_rooms_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:rooms:any")
async def clear_rooms(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "rooms", [])
    await _save_filters(state, filters)
    await open_rooms_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:price")
async def open_price_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    await callback.message.edit_text("<b>Цена</b>", reply_markup=build_price_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:price:max:"))
async def set_price_max(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    value_raw = callback.data.split(":")[-1]
    if not value_raw.isdigit():
        await callback.answer("Некорректная цена", show_alert=True)
        return
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "price_min", None)
    filters = update_object_filter(filters, "price_max", Decimal(int(value_raw) * 1_000_000))
    await _save_filters(state, filters)
    await callback.message.edit_text("<b>Цена</b>", reply_markup=build_price_filter_keyboard(filters))
    await callback.answer("Фильтр цены обновлен")


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:price:any")
async def clear_price(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "price_min", None)
    filters = update_object_filter(filters, "price_max", None)
    await _save_filters(state, filters)
    await open_price_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:price:manual")
async def manual_price_stub(callback: CallbackQuery) -> None:
    await callback.answer("Ручной ввод диапазона будет добавлен на следующем этапе.", show_alert=False)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:district")
async def open_district_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    selected = ", ".join(filters.get("districts", [])) or "нет"
    await callback.message.edit_text("<b>Район</b>\n\nВыбрано: " + selected, reply_markup=build_district_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:district:set:"))
async def toggle_district(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    district = callback.data.split(":", maxsplit=3)[-1]
    filters = await _get_filters(state)
    districts = set(filters.get("districts", []))
    if district in districts:
        districts.remove(district)
    else:
        districts.add(district)
    filters = update_object_filter(filters, "districts", sorted(districts))
    await _save_filters(state, filters)
    await open_district_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:district:any")
async def clear_districts(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "districts", [])
    await _save_filters(state, filters)
    await open_district_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:floor")
async def open_floor_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    await callback.message.edit_text("<b>Этаж</b>", reply_markup=build_floor_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:floor:"))
async def set_floor_mode(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    mode = callback.data.split(":")[-1]
    filters = await _get_filters(state)
    if mode == "any":
        filters = update_object_filter(filters, "floor_mode", None)
    else:
        filters = update_object_filter(filters, "floor_mode", mode)
    await _save_filters(state, filters)
    await callback.message.edit_text("<b>Этаж</b>", reply_markup=build_floor_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:sortmenu")
async def open_sort_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    await callback.message.edit_text("<b>Сортировка</b>", reply_markup=build_sort_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:sort:"))
async def set_sort_mode(callback: CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split(":")[-1]
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "sort", mode)
    await _save_filters(state, filters)
    await open_sort_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:type")
async def open_type_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    await callback.message.edit_text("<b>Тип объекта</b>", reply_markup=build_type_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:type:set:"))
async def set_type(callback: CallbackQuery, state: FSMContext) -> None:
    property_type = callback.data.split(":")[-1]
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "property_type", property_type)
    await _save_filters(state, filters)
    await open_type_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:type:any")
async def clear_type(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "property_type", None)
    await _save_filters(state, filters)
    await open_type_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:area")
async def open_area_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    await callback.message.edit_text("<b>Площадь</b>", reply_markup=build_area_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:area:set:"))
async def set_area_preset(callback: CallbackQuery, state: FSMContext) -> None:
    preset = callback.data.split(":")[-1]
    if preset not in AREA_PRESETS:
        await callback.answer("Некорректный диапазон", show_alert=True)
        return
    area_min, area_max = AREA_PRESETS[preset]
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "area_min", area_min)
    filters = update_object_filter(filters, "area_max", area_max)
    await _save_filters(state, filters)
    await open_area_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:area:any")
async def clear_area(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "area_min", None)
    filters = update_object_filter(filters, "area_max", None)
    await _save_filters(state, filters)
    await open_area_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:area:manual")
async def manual_area_stub(callback: CallbackQuery) -> None:
    await callback.answer("Ручной ввод площади будет добавлен на следующем этапе.", show_alert=False)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:date")
async def open_date_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    await callback.message.edit_text("<b>Дата добавления</b>", reply_markup=build_date_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:date:"))
async def set_date_mode(callback: CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split(":")[-1]
    filters = await _get_filters(state)
    if mode == "any":
        filters = update_object_filter(filters, "created_date_mode", None)
    else:
        filters = update_object_filter(filters, "created_date_mode", mode)
    await _save_filters(state, filters)
    await open_date_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:status")
async def open_status_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    filters = await _get_filters(state)
    await callback.message.edit_text("<b>Статус объекта</b>", reply_markup=build_status_filter_keyboard(filters))
    await callback.answer()


@router.callback_query(F.data.startswith(f"{OBJ_FILTER_PREFIX}:status:set:"))
async def toggle_status(callback: CallbackQuery, state: FSMContext) -> None:
    status = callback.data.split(":")[-1]
    filters = await _get_filters(state)
    statuses = set(filters.get("status", []))
    if status in statuses:
        statuses.remove(status)
    else:
        statuses.add(status)
    filters = update_object_filter(filters, "status", sorted(statuses) or ["active"])
    await _save_filters(state, filters)
    await open_status_menu(callback, state)


@router.callback_query(F.data == f"{OBJ_FILTER_PREFIX}:status:any")
async def clear_status(callback: CallbackQuery, state: FSMContext) -> None:
    filters = await _get_filters(state)
    filters = update_object_filter(filters, "status", [])
    await _save_filters(state, filters)
    await open_status_menu(callback, state)
