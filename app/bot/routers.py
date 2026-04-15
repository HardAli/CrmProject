from __future__ import annotations

from aiogram import Dispatcher, Router

from app.bot.handlers.clients.card import router as client_card_router
from app.bot.handlers.clients.edit import router as client_edit_router
from app.bot.handlers.clients.logs import router as client_logs_router
from app.bot.handlers.clients.create import router as client_create_router
from app.bot.handlers.clients.list import router as client_list_router
from app.bot.handlers.tasks.create import router as task_create_router
from app.bot.handlers.tasks.list_today import router as task_list_router
from app.bot.handlers.start import router as start_router


COMMON_ROUTERS: tuple[Router, ...] = (
    start_router,
    client_list_router,
    client_create_router,
    client_card_router,
    client_edit_router,
    client_logs_router,
    task_create_router,
    task_list_router,
)


def setup_routers(dispatcher: Dispatcher) -> None:
    for router in COMMON_ROUTERS:
        dispatcher.include_router(router)
