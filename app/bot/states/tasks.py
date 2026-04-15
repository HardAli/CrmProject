from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class TaskCreateStates(StatesGroup):
    title = State()
    description = State()
    due_at = State()


class NextContactStates(StatesGroup):
    value = State()