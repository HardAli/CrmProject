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
    floor = State()
    building_floors = State()
    wall_material = State()
    year_built = State()
    note = State()
    next_contact_at = State()
    seller_property_address = State()
    seller_property_price = State()
    seller_property_area = State()
    seller_property_kitchen_area = State()
    seller_property_rooms = State()
    seller_property_floor = State()
    seller_property_building_floors = State()
    seller_property_building_year = State()
    seller_property_building_material = State()
    seller_property_description = State()
    waiting_for_photos_after_create = State()


class ClientCardStates(StatesGroup):
    add_note = State()
    add_photo = State()


class ClientListStates(StatesGroup):
    search_query = State()
