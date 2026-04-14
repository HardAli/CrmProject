from __future__ import annotations

from app.common.dto.clients import CreateClientDTO
from app.database.models.client import Client
from app.repositories.clients import ClientRepository


class ClientService:
    def __init__(self, client_repository: ClientRepository) -> None:
        self._client_repository = client_repository

    async def create_client(self, data: CreateClientDTO) -> Client:
        return await self._client_repository.create(data)