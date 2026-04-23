from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.client_logs import ClientLogRepository
from app.repositories.client_properties import ClientPropertyRepository
from app.repositories.client_photo_repository import ClientPhotoRepository
from app.repositories.clients import ClientRepository
from app.repositories.tasks import TaskRepository
from app.repositories.properties import PropertyRepository
from app.repositories.statistics import StatisticsRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.clients import ClientService
from app.services.client_properties import ClientPropertyService
from app.services.client_photo_service import ClientPhotoService
from app.services.auto_link_service import AutoLinkService
from app.services.tasks import TaskService
from app.services.properties import PropertyService
from app.services.property_import_service import PropertyImportService
from app.services.property_photo_service import PropertyPhotoService
from app.services.parsers.krisha_parser import KrishaParser
from app.common.http.http_client import HttpClient
from app.services.search import SearchService
from app.services.statistics import StatisticsService


logger = logging.getLogger(__name__)


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
            client_log_repository = ClientLogRepository(session)
            task_repository = TaskRepository(session)
            property_repository = PropertyRepository(session)
            client_property_repository = ClientPropertyRepository(session)
            client_photo_repository = ClientPhotoRepository(session)
            statistics_repository = StatisticsRepository(session)

            data["session"] = session
            data["user_repository"] = user_repository
            data["client_repository"] = client_repository
            data["auth_service"] = AuthService(user_repository)
            data["client_log_repository"] = client_log_repository
            data["client_service"] = ClientService(client_repository, client_log_repository)
            data["task_repository"] = task_repository
            data["task_service"] = TaskService(task_repository, client_repository, client_log_repository)
            data["property_repository"] = property_repository
            data["property_service"] = PropertyService(property_repository)
            auto_link_service = AutoLinkService(
                client_repository=client_repository,
                client_property_repository=client_property_repository,
            )
            photo_service = PropertyPhotoService()
            data["property_import_service"] = PropertyImportService(
                property_service=data["property_service"],
                photo_service=photo_service,
                auto_link_service=auto_link_service,
                parsers=[KrishaParser(HttpClient())],
            )
            data["search_service"] = SearchService(client_repository, property_repository)
            data["client_property_repository"] = client_property_repository
            data["statistics_repository"] = statistics_repository
            data["statistics_service"] = StatisticsService(statistics_repository)
            data["client_photo_repository"] = client_photo_repository
            data["client_photo_service"] = ClientPhotoService(
                client_photo_repository=client_photo_repository,
                client_repository=client_repository,
            )
            data["client_property_service"] = ClientPropertyService(
                client_property_repository=client_property_repository,
                client_repository=client_repository,
                property_repository=property_repository,
                client_log_repository=client_log_repository,
            )

            try:
                return await handler(event, data)
            except SQLAlchemyError:
                logger.exception("Database error in update handler, rolling back session")
                await session.rollback()
                raise
