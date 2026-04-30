from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PropertyCreateStates(StatesGroup):
    title = State()
    property_type = State()
    district = State()
    address = State()
    owner_phone = State()
    price = State()
    area = State()
    kitchen_area = State()
    rooms = State()
    floor = State()
    building_floors = State()
    building_year = State()
    building_material = State()
    description = State()
    link = State()
    status = State()
    duplicate_confirm = State()


class PropertyListStates(StatesGroup):
    search_query = State()


class PropertyCallCarouselStates(StatesGroup):
    waiting_for_note = State()
    waiting_for_price = State()


class PropertyEditStates(StatesGroup):
    choosing_field = State()
    waiting_for_value = State()
