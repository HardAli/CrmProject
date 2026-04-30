from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.properties import get_property_actions_inline_keyboard_with_access, get_property_edit_choice_keyboard, get_property_edit_menu_keyboard
from app.bot.states.properties import PropertyEditStates
from app.common.enums import PropertyType
from app.common.formatters.property_formatter import format_property_card
from app.services.auth_service import AuthService
from app.services.properties import PropertyService

router = Router(name="property_edit")

@router.callback_query(F.data.startswith("property_edit:"))
async def open_edit(callback: CallbackQuery, state: FSMContext, auth_service: AuthService, property_service: PropertyService) -> None:
    if callback.message is None: return
    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None: return
    pid = int(callback.data.split(":",1)[1])
    prop = await property_service.get_property_for_edit(current_user=user, property_id=pid)
    if prop is None:
        await callback.answer("Нет прав на редактирование", show_alert=True); return
    await state.set_state(PropertyEditStates.choosing_field)
    await state.update_data(property_id=pid)
    await callback.message.answer("Выберите поле для редактирования:", reply_markup=get_property_edit_menu_keyboard(property_id=pid, is_apartment=prop.property_type == PropertyType.APARTMENT))
    await callback.answer()

@router.callback_query(F.data.startswith("prop_edit:menu:"))
async def back_menu(callback: CallbackQuery, auth_service: AuthService, property_service: PropertyService) -> None:
    if callback.message is None: return
    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id); pid=int(callback.data.split(':')[2])
    prop = await property_service.get_property_for_view(current_user=user, property_id=pid) if user else None
    if prop is None: return
    await callback.message.answer("Меню редактирования:", reply_markup=get_property_edit_menu_keyboard(property_id=pid, is_apartment=prop.property_type == PropertyType.APARTMENT))
    await callback.answer()

@router.callback_query(F.data.startswith("prop_edit:field:"))
async def choose_field(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None: return
    _,_,pid,field = callback.data.split(':',3)
    await state.set_state(PropertyEditStates.waiting_for_value)
    await state.update_data(property_id=int(pid), field_name=field)
    await callback.message.answer(f"Выберите/введите новое значение для поля: {field}", reply_markup=get_property_edit_choice_keyboard(property_id=int(pid), field_name=field))
    await callback.answer()

@router.callback_query(F.data.startswith("prop_edit:value:"))
async def quick_value(callback: CallbackQuery, state: FSMContext, auth_service: AuthService, property_service: PropertyService, session: AsyncSession) -> None:
    if callback.message is None: return
    _,_,pid,field,val = callback.data.split(':',4)
    await _save(callback.message, int(pid), field, val, state, auth_service, property_service, session)
    await callback.answer()

@router.callback_query(F.data.startswith("prop_edit:manual:"))
async def manual_value(callback: CallbackQuery, state: FSMContext) -> None:
    _,_,pid,field = callback.data.split(':',3)
    await state.set_state(PropertyEditStates.waiting_for_value)
    await state.update_data(property_id=int(pid), field_name=field)
    await callback.message.answer("Введите новое значение текстом.")
    await callback.answer()

@router.message(PropertyEditStates.waiting_for_value)
async def process_manual(message: Message, state: FSMContext, auth_service: AuthService, property_service: PropertyService, session: AsyncSession) -> None:
    data = await state.get_data()
    await _save(message, int(data['property_id']), str(data['field_name']), message.text or "", state, auth_service, property_service, session)

async def _save(target: Message, property_id: int, field_name: str, raw: str, state: FSMContext, auth_service: AuthService, property_service: PropertyService, session: AsyncSession) -> None:
    if target.from_user is None: return
    user = await auth_service.get_active_user_by_telegram_id(target.from_user.id)
    if user is None: return
    try:
        prop = await property_service.update_property_field(current_user=user, property_id=property_id, field_name=field_name, raw_value=raw)
    except (PermissionError, ValueError) as exc:
        await target.answer(f"❌ {exc}")
        return
    await session.commit()
    await target.answer("✅ Поле обновлено.")
    await target.answer("Продолжайте редактирование:", reply_markup=get_property_edit_menu_keyboard(property_id=property_id, is_apartment=prop.property_type == PropertyType.APARTMENT))
