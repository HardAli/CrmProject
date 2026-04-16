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
    rooms = State()
    floor = State()
    building_floors = State()
    description = State()
    link = State()
    status = State()