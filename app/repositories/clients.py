from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dto.clients import CreateClientDTO
from app.database.models.client import Client


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CreateClientDTO) -> Client:
        client = Client(
            full_name=data.full_name,
            phone=data.phone,
            source=data.source,
            request_type=data.request_type,
            property_type=data.property_type,
            district=data.district,
            rooms=data.rooms,
            budget_min=data.budget_min,
            budget_max=data.budget_max,
            note=data.note,
            next_contact_at=data.next_contact_at,
            manager_id=data.manager_id,
        )
        self._session.add(client)
        await self._session.flush()
        await self._session.refresh(client)
        return client