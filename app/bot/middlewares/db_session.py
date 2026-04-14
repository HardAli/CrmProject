from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.clients import ClientRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.clients import ClientService


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        async with self._session_factory() as session:
            user_repository = UserRepository(session)
            client_repository = ClientRepository(session)

            data["session"] = session
            data["user_repository"] = user_repository
            data["client_repository"] = client_repository
            data["auth_service"] = AuthService(user_repository)
            data["client_service"] = ClientService(client_repository)

            return await handler(event, data)
