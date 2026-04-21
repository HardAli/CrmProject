from app.bot.handlers.clients.card import router as client_card_router
from app.bot.handlers.clients.create import router as client_create_router
from app.bot.handlers.clients.edit import router as client_edit_router
from app.bot.handlers.clients.list import router as client_list_router
from app.bot.handlers.clients.logs import router as client_logs_router
from app.bot.handlers.clients.properties import router as client_properties_router
from app.bot.handlers.clients.photos import router as client_photos_router

__all__ = (
    "client_list_router",
    "client_create_router",
    "client_card_router",
    "client_edit_router",
    "client_logs_router",
    "client_properties_router",
    "client_photos_router",
)