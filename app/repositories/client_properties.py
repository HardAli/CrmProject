from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.enums import ClientPropertyRelationStatus
from app.database.models.client import Client
from app.database.models.client_property import ClientProperty
from app.database.models.property import Property


class ClientPropertyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        client_id: int,
        property_id: int,
        relation_status: ClientPropertyRelationStatus,
    ) -> ClientProperty:
        link = ClientProperty(
            client_id=client_id,
            property_id=property_id,
            relation_status=relation_status,
        )
        self._session.add(link)
        await self._session.flush()
        await self._session.refresh(link)
        return link

    async def get_by_id(self, link_id: int) -> ClientProperty | None:
        stmt = (
            select(ClientProperty)
            .options(
                joinedload(ClientProperty.client).joinedload(Client.manager),
                joinedload(ClientProperty.property).joinedload(Property.manager),
            )
            .where(ClientProperty.id == link_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_client(self, client_id: int, limit: int = 10) -> Sequence[ClientProperty]:
        stmt = (
            select(ClientProperty)
            .options(
                joinedload(ClientProperty.client).joinedload(Client.manager),
                joinedload(ClientProperty.property).joinedload(Property.manager),
            )
            .where(ClientProperty.client_id == client_id)
            .order_by(ClientProperty.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_existing(self, client_id: int, property_id: int) -> ClientProperty | None:
        stmt = (
            select(ClientProperty)
            .options(
                joinedload(ClientProperty.client).joinedload(Client.manager),
                joinedload(ClientProperty.property).joinedload(Property.manager),
            )
            .where(
                ClientProperty.client_id == client_id,
                ClientProperty.property_id == property_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_relation_status(
        self,
        *,
        link: ClientProperty,
        new_status: ClientPropertyRelationStatus,
    ) -> ClientProperty:
        link.relation_status = new_status
        await self._session.flush()
        await self._session.refresh(link)
        return link