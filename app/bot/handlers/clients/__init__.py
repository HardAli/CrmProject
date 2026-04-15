from app.bot.handlers.clients.card import router as client_card_router
from app.bot.handlers.clients.create import router as client_create_router
from app.bot.handlers.clients.list import router as client_list_router

__all__ = ("client_list_router", "client_create_router", "client_card_router")