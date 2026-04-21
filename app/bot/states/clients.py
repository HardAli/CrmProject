from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ClientCreateStates(StatesGroup):
    full_name = State()
    phone = State()
    source = State()
    request_type = State()
    property_type = State()
    district = State()
    rooms = State()
    budget = State()
    note = State()
    next_contact_at = State()


class ClientCardStates(StatesGroup):
    add_note = State()
