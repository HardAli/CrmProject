from __future__ import annotations

from aiogram import Dispatcher, Router

from app.bot.handlers.start import router as start_router


COMMON_ROUTERS: tuple[Router, ...] = (
    start_router,
)


def setup_routers(dispatcher: Dispatcher) -> None:
    for router in COMMON_ROUTERS:
        dispatcher.include_router(router)