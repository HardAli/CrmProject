from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    choose_mode = State()

    client_quick_query = State()
    client_full_name = State()
    client_phone = State()
    client_district = State()
    client_status = State()
    client_request_type = State()

    property_quick_query = State()
    property_title = State()
    property_district = State()
    property_type = State()
    property_status = State()
    property_price_min = State()
    property_price_max = State()
    property_rooms = State()