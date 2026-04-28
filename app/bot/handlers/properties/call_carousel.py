from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.properties import CALL_CAROUSEL_TEXT, get_properties_menu_keyboard
from app.bot.keyboards.property_call_carousel import (
    CALL_MODE_DEFAULT,
    get_call_card_keyboard,
    get_call_finished_keyboard,
    get_call_menu_keyboard,
    get_call_more_keyboard,
    get_no_answer_keyboard,
    get_note_cancel_keyboard,
    get_reject_reason_keyboard,
    get_sold_confirm_keyboard,
)
from app.common.formatters.property_formatter import format_price_compact, format_property_call_card
from app.common.utils.phone_links import format_phone_for_copy_plain
from app.services.auth_service import AuthService
from app.bot.states.properties import PropertyCallCarouselStates
from app.services.properties import PropertyService
from app.services.property_call_service import PropertyCallService

router = Router(name="property_call_carousel")



async def _get_user(callback: CallbackQuery, auth_service: AuthService):
    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
    return user


async def _render_current_card(
    callback: CallbackQuery,
    *,
    state: FSMContext,
    auth_service: AuthService,
    property_service: PropertyService,
    call_service: PropertyCallService,
) -> None:
    data = await state.get_data()
    current_property_id = data.get("current_property_id")
    if not isinstance(current_property_id, int):
        await callback.answer("Объект не найден", show_alert=True)
        return

    user = await _get_user(callback, auth_service)
    if user is None:
        return

    property_obj = await property_service.get_property_for_view(current_user=user, property_id=current_property_id)
    if property_obj is None:
        await callback.answer("Объект не найден", show_alert=True)
        return

    mode = str(data.get("call_carousel_mode") or CALL_MODE_DEFAULT)
    shown_ids = [int(v) for v in data.get("shown_property_ids", []) if isinstance(v, int)]
    queue_count = await call_service.get_call_queue_count(current_user=user, mode=mode, exclude_ids=shown_ids)
    stats = await call_service.get_call_menu_stats(current_user=user)
    position = int(data.get("current_position") or 1)
    total = position + queue_count
    text = format_property_call_card(property_obj=property_obj, position=position, total=total, today_stats=stats)

    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=get_call_card_keyboard(property_id=property_obj.id, phone=property_obj.owner_phone), parse_mode=None)


async def _show_next_property(
    callback: CallbackQuery,
    *,
    state: FSMContext,
    auth_service: AuthService,
    property_service: PropertyService,
    call_service: PropertyCallService,
) -> None:
    user = await _get_user(callback, auth_service)
    if user is None:
        return

    data = await state.get_data()
    mode = str(data.get("call_carousel_mode") or CALL_MODE_DEFAULT)
    shown_ids = [int(v) for v in data.get("shown_property_ids", []) if isinstance(v, int)]

    property_obj = await call_service.get_next_property_for_call(current_user=user, mode=mode, exclude_ids=shown_ids)
    if property_obj is None:
        stats = await call_service.get_call_menu_stats(current_user=user)
        text = (
            "📞 Прозвон завершён.\n\n"
            "Сегодня:\n"
            f"✅ Договорился: {stats.get('AGREED', 0)}\n"
            f"📵 Недозвон: {stats.get('NO_ANSWER', 0)}\n"
            f"❌ Отказали: {stats.get('REJECTED', 0)}\n"
            f"🏁 Продано: {stats.get('SOLD', 0)}"
        )
        if callback.message is not None:
            await callback.message.edit_text(text, reply_markup=get_call_finished_keyboard(), parse_mode=None)
        await callback.answer()
        return

    shown_ids.append(property_obj.id)
    position = len(shown_ids)
    await state.update_data(
        call_carousel_mode=mode,
        shown_property_ids=shown_ids,
        current_property_id=property_obj.id,
        current_position=position,
    )

    queue_count = await call_service.get_call_queue_count(current_user=user, mode=mode, exclude_ids=shown_ids)
    stats = await call_service.get_call_menu_stats(current_user=user)
    text = format_property_call_card(property_obj=property_obj, position=position, total=position + queue_count, today_stats=stats)

    if callback.message is not None:
        await callback.message.edit_text(
            text,
            reply_markup=get_call_card_keyboard(property_id=property_obj.id, phone=property_obj.owner_phone),
            parse_mode=None,
        )
    await callback.answer()


@router.message(F.text == CALL_CAROUSEL_TEXT)
async def open_call_menu_message(message: Message, auth_service: AuthService, call_service: PropertyCallService) -> None:
    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Нет доступа")
        return
    stats = await call_service.get_call_menu_stats(current_user=user)
    text = (
        "📞 Прозвон объектов\n\n"
        "Сегодня:\n"
        f"✅ Договорился: {stats.get('AGREED', 0)}\n"
        f"📵 Недозвон: {stats.get('NO_ANSWER', 0)}\n"
        f"❌ Отказали: {stats.get('REJECTED', 0)}\n"
        f"🏁 Продано: {stats.get('SOLD', 0)}"
    )
    await message.answer(text, reply_markup=get_call_menu_keyboard(), parse_mode=None)


@router.callback_query(F.data == "callmenu")
async def open_call_menu_callback(callback: CallbackQuery, auth_service: AuthService, call_service: PropertyCallService, state: FSMContext) -> None:
    user = await _get_user(callback, auth_service)
    if user is None:
        return
    await state.clear()
    stats = await call_service.get_call_menu_stats(current_user=user)
    text = (
        "📞 Прозвон объектов\n\n"
        "Сегодня:\n"
        f"✅ Договорился: {stats.get('AGREED', 0)}\n"
        f"📵 Недозвон: {stats.get('NO_ANSWER', 0)}\n"
        f"❌ Отказали: {stats.get('REJECTED', 0)}\n"
        f"🏁 Продано: {stats.get('SOLD', 0)}\n"
        f"⏭ Пропущено: {stats.get('SKIPPED', 0)}"
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=get_call_menu_keyboard(), parse_mode=None)
    await callback.answer()


@router.callback_query(F.data.startswith("callstart:"))
async def start_call_mode(callback: CallbackQuery, state: FSMContext, auth_service: AuthService, property_service: PropertyService, call_service: PropertyCallService) -> None:
    mode = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(call_carousel_mode=mode, shown_property_ids=[], current_position=0)
    await _show_next_property(
        callback,
        state=state,
        auth_service=auth_service,
        property_service=property_service,
        call_service=call_service,
    )


@router.callback_query(F.data.startswith("callcopy:"))
async def copy_call_phone(callback: CallbackQuery, auth_service: AuthService, property_service: PropertyService) -> None:
    if callback.message is None:
        await callback.answer()
        return
    user = await _get_user(callback, auth_service)
    if user is None:
        return

    property_id = int(callback.data.split(":")[1])
    property_obj = await property_service.get_property_for_view(current_user=user, property_id=property_id)
    if property_obj is None:
        await callback.answer("Объект не найден", show_alert=True)
        return

    phone = format_phone_for_copy_plain(property_obj.owner_phone)
    if phone == "—":
        await callback.answer("Номер не найден", show_alert=True)
        return

    await callback.message.answer(phone, parse_mode=None)
    await callback.answer()


@router.callback_query(F.data.startswith("callmore:"))
async def open_more_menu(callback: CallbackQuery) -> None:
    property_id = int(callback.data.split(":")[1])
    if callback.message is not None:
        await callback.message.edit_reply_markup(reply_markup=get_call_more_keyboard(property_id))
    await callback.answer()


@router.callback_query(F.data.startswith("callbacktocard:"))
async def back_to_call_card(callback: CallbackQuery, state: FSMContext, auth_service: AuthService, property_service: PropertyService, call_service: PropertyCallService) -> None:
    await _render_current_card(
        callback,
        state=state,
        auth_service=auth_service,
        property_service=property_service,
        call_service=call_service,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("callres:") & ~F.data.endswith(":agreed"))
async def handle_call_result(callback: CallbackQuery) -> None:
    property_id = int(callback.data.split(":")[1])
    result = callback.data.split(":")[2]
    if callback.message is None:
        await callback.answer()
        return
    if result == "no_answer":
        await callback.message.edit_reply_markup(reply_markup=get_no_answer_keyboard(property_id))
    elif result == "rejected":
        await callback.message.edit_reply_markup(reply_markup=get_reject_reason_keyboard(property_id))
    else:
        await callback.answer()


@router.callback_query(F.data.startswith("callnoans:"))
async def save_no_answer(callback: CallbackQuery, auth_service: AuthService, call_service: PropertyCallService, property_service: PropertyService, state: FSMContext, session: AsyncSession) -> None:
    _, raw_property_id, option = callback.data.split(":", maxsplit=2)
    user = await _get_user(callback, auth_service)
    if user is None:
        return
    next_call_at = call_service.calc_no_answer_next_call(option)
    await call_service.save_call_result(
        property_id=int(raw_property_id),
        current_user=user,
        result="NO_ANSWER",
        next_call_at=next_call_at,
    )
    await session.commit()
    await _show_next_property(callback, state=state, auth_service=auth_service, property_service=property_service, call_service=call_service)


@router.callback_query(F.data.startswith("callrej:"))
async def save_rejected(callback: CallbackQuery, auth_service: AuthService, call_service: PropertyCallService, property_service: PropertyService, state: FSMContext, session: AsyncSession) -> None:
    _, raw_property_id, reason = callback.data.split(":", maxsplit=2)
    user = await _get_user(callback, auth_service)
    if user is None:
        return
    reason_map = {
        "no_cooperation": "NO_COOPERATION",
        "not_actual": "NOT_ACTUAL",
        "wrong_number": "WRONG_NUMBER",
        "other": "OTHER",
        "skip": None,
    }
    mapped_reason = reason_map.get(reason)
    comment = "Не тот номер" if mapped_reason == "WRONG_NUMBER" else None
    await call_service.save_call_result(
        property_id=int(raw_property_id),
        current_user=user,
        result="REJECTED",
        reason=mapped_reason,
        comment=comment,
        next_call_at=None,
    )
    await session.commit()
    await _show_next_property(callback, state=state, auth_service=auth_service, property_service=property_service, call_service=call_service)


@router.callback_query(F.data.startswith("callnext:"))
async def skip_property(callback: CallbackQuery, auth_service: AuthService, call_service: PropertyCallService, property_service: PropertyService, state: FSMContext, session: AsyncSession) -> None:
    property_id = int(callback.data.split(":")[1])
    user = await _get_user(callback, auth_service)
    if user is None:
        return
    await call_service.save_call_result(property_id=property_id, current_user=user, result="SKIPPED")
    await session.commit()
    await _show_next_property(callback, state=state, auth_service=auth_service, property_service=property_service, call_service=call_service)


@router.callback_query(F.data.startswith("callres:") & F.data.endswith(":agreed"))
async def save_agreed(callback: CallbackQuery, auth_service: AuthService, call_service: PropertyCallService, property_service: PropertyService, state: FSMContext, session: AsyncSession) -> None:
    property_id = int(callback.data.split(":")[1])
    user = await _get_user(callback, auth_service)
    if user is None:
        return
    await call_service.save_call_result(property_id=property_id, current_user=user, result="AGREED")
    await session.commit()
    await _show_next_property(callback, state=state, auth_service=auth_service, property_service=property_service, call_service=call_service)


@router.callback_query(F.data.startswith("callsold:"))
async def ask_sold_confirm(callback: CallbackQuery) -> None:
    property_id = int(callback.data.split(":")[1])
    if callback.message is not None:
        await callback.message.edit_text("Точно отметить объект как проданный?", reply_markup=get_sold_confirm_keyboard(property_id), parse_mode=None)
    await callback.answer()


@router.callback_query(F.data.startswith("callsold_confirm:"))
async def save_sold(callback: CallbackQuery, auth_service: AuthService, call_service: PropertyCallService, property_service: PropertyService, state: FSMContext, session: AsyncSession) -> None:
    property_id = int(callback.data.split(":")[1])
    user = await _get_user(callback, auth_service)
    if user is None:
        return
    await call_service.mark_property_sold_from_call(property_id=property_id, current_user=user)
    await session.commit()
    await _show_next_property(callback, state=state, auth_service=auth_service, property_service=property_service, call_service=call_service)


@router.callback_query(F.data.startswith("callsold_cancel:"))
async def cancel_sold(callback: CallbackQuery, state: FSMContext, auth_service: AuthService, property_service: PropertyService, call_service: PropertyCallService) -> None:
    await _render_current_card(
        callback,
        state=state,
        auth_service=auth_service,
        property_service=property_service,
        call_service=call_service,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("callnote:"))
async def ask_note(callback: CallbackQuery, state: FSMContext) -> None:
    property_id = int(callback.data.split(":")[1])
    await state.set_state(PropertyCallCarouselStates.waiting_for_note)
    await state.update_data(current_property_id=property_id)
    if callback.message is not None:
        await callback.message.answer("Напишите заметку по объекту:", reply_markup=get_note_cancel_keyboard(property_id), parse_mode=None)
    await callback.answer()


@router.message(PropertyCallCarouselStates.waiting_for_note)
async def save_note(message: Message, state: FSMContext, auth_service: AuthService, call_service: PropertyCallService, session: AsyncSession) -> None:
    if (message.text or "").strip().lower() == "отмена":
        await state.clear()
        await message.answer("Отменено.")
        return
    data = await state.get_data()
    property_id = data.get("current_property_id")
    if not isinstance(property_id, int):
        await message.answer("Объект не найден")
        return
    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Нет доступа")
        return
    await call_service.add_call_note(property_id=property_id, current_user=user, note=(message.text or "").strip())
    await session.commit()
    await state.clear()
    await message.answer("✅ Заметка сохранена.")


@router.callback_query(F.data.startswith("callprice:"))
async def ask_price(callback: CallbackQuery, state: FSMContext) -> None:
    property_id = int(callback.data.split(":")[1])
    await state.set_state(PropertyCallCarouselStates.waiting_for_price)
    await state.update_data(current_property_id=property_id)
    if callback.message is not None:
        await callback.message.answer("Введите новую цену, например 18.5 или 18 500 000:", reply_markup=get_note_cancel_keyboard(property_id), parse_mode=None)
    await callback.answer()


@router.message(PropertyCallCarouselStates.waiting_for_price)
async def save_price(message: Message, state: FSMContext, auth_service: AuthService, call_service: PropertyCallService, session: AsyncSession) -> None:
    data = await state.get_data()
    property_id = data.get("current_property_id")
    if not isinstance(property_id, int):
        await message.answer("Объект не найден")
        return
    price = call_service.parse_price_value((message.text or "").strip())
    if price is None:
        await message.answer("Введите цену, например 18.5 или 18 500 000.")
        return
    user = await auth_service.get_active_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Нет доступа")
        return
    old_price, new_price = await call_service.update_property_price_from_call(property_id=property_id, current_user=user, price=price)
    await session.commit()
    await state.clear()
    await message.answer(f"✅ Цена изменена: {format_price_compact(old_price)} -> {format_price_compact(new_price)}")


@router.callback_query(F.data.startswith("callcard:"))
async def open_property_card_from_call(callback: CallbackQuery) -> None:
    property_id = int(callback.data.split(":")[1])
    if callback.message is not None:
        await callback.message.answer(
            "Открыть подробную карточку:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="📄 Карточка", callback_data=f"property_view:{property_id}")]]
            ),
            parse_mode=None,
        )
    await callback.answer()


@router.callback_query(F.data == "callpause")
async def pause_call(callback: CallbackQuery) -> None:
    await callback.answer("Прозвон на паузе")


@router.callback_query(F.data == "callstats")
async def show_call_stats(callback: CallbackQuery, auth_service: AuthService, call_service: PropertyCallService) -> None:
    user = await _get_user(callback, auth_service)
    if user is None:
        return
    stats = await call_service.get_call_menu_stats(current_user=user)
    text = (
        "📊 Статистика за сегодня\n\n"
        f"✅ Договорился: {stats.get('AGREED', 0)}\n"
        f"📵 Недозвон: {stats.get('NO_ANSWER', 0)}\n"
        f"❌ Отказали: {stats.get('REJECTED', 0)}\n"
        f"🏁 Продано: {stats.get('SOLD', 0)}\n"
        f"⏭ Пропущено: {stats.get('SKIPPED', 0)}"
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=get_call_menu_keyboard(), parse_mode=None)
    await callback.answer()


@router.callback_query(F.data == "callmenu_exit")
async def exit_call_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message is not None:
        await callback.message.answer("Раздел объектов. Выберите действие:", reply_markup=get_properties_menu_keyboard())
    await callback.answer()
