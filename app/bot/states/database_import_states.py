from aiogram.fsm.state import State, StatesGroup


class DatabaseImportStates(StatesGroup):
    waiting_for_archive = State()