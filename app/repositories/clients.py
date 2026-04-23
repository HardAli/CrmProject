from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time, timezone

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.dto.clients import CreateClientDTO
from app.common.enums import ClientStatus, RequestType
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
            budget=data.budget,
            floor=data.floor,
            building_floors=data.building_floors,
            wall_material=data.wall_material,
            year_built=data.year_built,
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

    async def update_status(self, client: Client, new_status: ClientStatus) -> Client:
        client.status = new_status
        await self._session.flush()
        await self._session.refresh(client)
        return client

    async def update_note(self, client: Client, note: str) -> Client:
        client.note = note
        await self._session.flush()
        await self._session.refresh(client)
        return client

    async def update_next_contact(self, client: Client, next_contact_at: datetime | None) -> Client:
        client.next_contact_at = next_contact_at
        await self._session.flush()
        await self._session.refresh(client)
        return client

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

    async def get_today_contacts_for_user(
            self,
            *,
            user_id: int,
            target_date: date,
            limit: int = 20,
    ) -> Sequence[Client]:
        return await self.get_contacts_for_date(manager_id=user_id, target_date=target_date, limit=limit)

    async def get_overdue_contacts_for_user(
            self,
            *,
            user_id: int,
            now_dt: datetime,
            limit: int = 20,
    ) -> Sequence[Client]:
        return await self.get_overdue_contacts(manager_id=user_id, now_dt=now_dt, limit=limit)

    async def get_contacts_for_date(
            self,
            *,
            manager_id: int | None,
            target_date: date,
            limit: int = 20,
    ) -> Sequence[Client]:
        day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        stmt = self._base_list_query().where(
            Client.next_contact_at.is_not(None),
            Client.next_contact_at >= day_start,
            Client.next_contact_at <= day_end,
        )
        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_overdue_contacts(
            self,
            *,
            manager_id: int | None,
            now_dt: datetime,
            limit: int = 20,
    ) -> Sequence[Client]:
        stmt = self._base_list_query().where(
            Client.next_contact_at.is_not(None),
            Client.next_contact_at < now_dt,
        )
        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def exists_for_manager(self, client_id: int, manager_id: int) -> bool:
        stmt = select(Client.id).where(Client.id == client_id, Client.manager_id == manager_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def search_clients(
            self,
            *,
            full_name: str | None = None,
            phone: str | None = None,
            district: str | None = None,
            status: ClientStatus | None = None,
            request_type: RequestType | None = None,
            manager_id: int | None = None,
            limit: int = 10,
    ) -> Sequence[Client]:
        stmt = self._base_list_query()

        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)
        if full_name and phone and district and full_name == phone == district:
            quick_query = full_name
            stmt = stmt.where(
                or_(
                    Client.full_name.ilike(f"%{quick_query}%"),
                    Client.phone.ilike(f"%{quick_query}%"),
                    Client.district.ilike(f"%{quick_query}%"),
                )
            )
        else:
            if full_name:
                stmt = stmt.where(Client.full_name.ilike(f"%{full_name}%"))
            if phone:
                stmt = stmt.where(Client.phone.ilike(f"%{phone}%"))
            if district:
                stmt = stmt.where(Client.district.ilike(f"%{district}%"))
        if status:
            stmt = stmt.where(Client.status == status)
        if request_type:
            stmt = stmt.where(Client.request_type == request_type)

        result = await self._session.execute(stmt.limit(limit))
        return result.scalars().all()

    async def get_by_phone_candidates(self, candidates: list[str], manager_id: int | None = None) -> Sequence[Client]:
        if not candidates:
            return []
        stmt = self._base_list_query().where(Client.phone.in_(candidates))
        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)
        result = await self._session.execute(stmt.limit(100))
        return result.scalars().all()

    @staticmethod
    def _base_list_query() -> Select[tuple[Client]]:
        return select(Client).options(joinedload(Client.manager)).order_by(Client.created_at.desc())