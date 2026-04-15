from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.dto.clients import CreateClientDTO
from app.common.enums import ClientStatus
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

    async def get_by_id(self, client_id: int) -> Client | None:
        stmt = (
            select(Client)
            .options(joinedload(Client.manager))
            .where(Client.id == client_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_manager(self, manager_id: int, limit: int = 10, offset: int = 0) -> Sequence[Client]:
        stmt = self._base_list_query().where(Client.manager_id == manager_id)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_status(
            self,
            status: ClientStatus,
            manager_id: int | None = None,
            limit: int = 10,
            offset: int = 0,
    ) -> Sequence[Client]:
        stmt = self._base_list_query().where(Client.status == status)
        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_recent(self, limit: int = 10, manager_id: int | None = None) -> Sequence[Client]:
        stmt = self._base_list_query()
        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def exists_for_manager(self, client_id: int, manager_id: int) -> bool:
        stmt = select(Client.id).where(Client.id == client_id, Client.manager_id == manager_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _base_list_query() -> Select[tuple[Client]]:
        return select(Client).order_by(Client.created_at.desc())
