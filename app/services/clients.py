from __future__ import annotations

from collections.abc import Sequence

from app.common.dto.clients import CreateClientDTO
from app.common.enums import ClientStatus, UserRole
from app.database.models.client import Client
from app.database.models.user import User
from app.repositories.clients import ClientRepository


class ClientService:
    def __init__(self, client_repository: ClientRepository) -> None:
        self._client_repository = client_repository

    async def create_client(self, data: CreateClientDTO) -> Client:
        return await self._client_repository.create(data)

    async def get_my_clients(self, current_user: User, limit: int = 10) -> Sequence[Client]:
        if current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            return await self._client_repository.get_recent(limit=limit)
        return await self._client_repository.get_by_manager(manager_id=current_user.id, limit=limit)

    async def get_clients_by_status(self, current_user: User, status: ClientStatus, limit: int = 10) -> Sequence[Client]:
        manager_id = None if self._can_view_all(current_user) else current_user.id
        return await self._client_repository.get_by_status(
            status=status,
            manager_id=manager_id,
            limit=limit,
        )

    async def get_recent_clients(self, current_user: User, limit: int = 10) -> Sequence[Client]:
        manager_id = None if self._can_view_all(current_user) else current_user.id
        return await self._client_repository.get_recent(limit=limit, manager_id=manager_id)

    async def get_client_for_view(self, current_user: User, client_id: int) -> Client | None:
        client = await self._client_repository.get_by_id(client_id)
        if client is None:
            return None

        if self._can_view_all(current_user):
            return client

        if client.manager_id != current_user.id:
            return None

        return client

    @staticmethod
    def _can_view_all(current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}