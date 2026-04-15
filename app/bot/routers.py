from __future__ import annotations

from aiogram import Dispatcher, Router

from app.bot.handlers.clients.card import router as client_card_router
from app.bot.handlers.clients.create import router as client_create_router
from app.bot.handlers.clients.list import router as client_list_router
from app.bot.handlers.start import router as start_router


COMMON_ROUTERS: tuple[Router, ...] = (
    start_router,
    client_list_router,
    client_create_router,
    client_card_router,
)


def setup_routers(dispatcher: Dispatcher) -> None:
    for router in COMMON_ROUTERS:
        dispatcher.include_router(router)
