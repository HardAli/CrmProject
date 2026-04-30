from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PropertyImportStates(StatesGroup):
    waiting_for_url = State()
    preview = State()
    fill_missing = State()
    duplicate_confirm = State()
