from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import Select, and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.dto.clients import CreateClientDTO
from app.common.enums import ClientStatus, RequestType, TaskStatus
from app.database.models.client import Client
from app.database.models.client_property import ClientProperty
from app.database.models.task import Task


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

    async def get_by_phone_normalized(self, phone_normalized: str) -> Client | None:
        candidates = {phone_normalized}
        if phone_normalized.startswith("+"):
            candidates.add(phone_normalized.replace("+", "8", 1))
        if phone_normalized.startswith("8"):
            candidates.add(phone_normalized.replace("8", "+", 1))

        stmt = self._base_list_query().where(Client.phone.in_(candidates)).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_phone_normalized(self, phone_normalized: str) -> Sequence[Client]:
        candidates = {phone_normalized}
        if phone_normalized.startswith("+"):
            candidates.add(phone_normalized.replace("+", "8", 1))
        if phone_normalized.startswith("8"):
            candidates.add(phone_normalized.replace("8", "+", 1))
        stmt = self._base_list_query().where(Client.phone.in_(candidates)).limit(200)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_filtered(
        self,
        *,
        filters: dict,
        manager_id: int | None,
        page: int,
        per_page: int,
    ) -> tuple[list[Client], int]:
        stmt = select(Client).options(joinedload(Client.manager))
        stmt = self.apply_client_filters(stmt=stmt, filters=filters, manager_id=manager_id)
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total_count = int((await self._session.execute(count_stmt)).scalar_one())
        stmt = self.apply_client_sorting(stmt=stmt, filters=filters)
        stmt = stmt.limit(per_page).offset((page - 1) * per_page)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total_count

    def apply_client_filters(
        self,
        *,
        stmt: Select[tuple[Client]],
        filters: dict,
        manager_id: int | None,
    ) -> Select[tuple[Client]]:
        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)

        statuses = filters.get("statuses") or []
        if statuses:
            stmt = stmt.where(Client.status.in_([ClientStatus(value) for value in statuses]))

        deal_types = filters.get("deal_types") or []
        if deal_types:
            stmt = stmt.where(Client.request_type.in_([RequestType(value) for value in deal_types]))

        rooms = filters.get("rooms") or []
        if rooms:
            stmt = stmt.where(or_(*[Client.rooms.ilike(f"%{room}%") for room in rooms]))

        budget_min = filters.get("budget_min")
        budget_max = filters.get("budget_max")
        if budget_min is not None:
            stmt = stmt.where(Client.budget.is_not(None), Client.budget >= budget_min)
        if budget_max is not None:
            stmt = stmt.where(Client.budget.is_not(None), Client.budget <= budget_max)

        districts = filters.get("districts") or []
        if districts:
            stmt = stmt.where(or_(*[Client.district.ilike(f"%{district}%") for district in districts]))

        now_utc = datetime.now(timezone.utc)
        today_start = datetime.combine(now_utc.date(), time.min, tzinfo=timezone.utc)
        tomorrow_start = today_start + timedelta(days=1)
        day_after_tomorrow_start = tomorrow_start + timedelta(days=1)
        week_end = today_start + timedelta(days=7)
        next_contact_mode = filters.get("next_contact_mode")
        if next_contact_mode == "today":
            stmt = stmt.where(Client.next_contact_at >= today_start, Client.next_contact_at < tomorrow_start)
        elif next_contact_mode == "tomorrow":
            stmt = stmt.where(Client.next_contact_at >= tomorrow_start, Client.next_contact_at < day_after_tomorrow_start)
        elif next_contact_mode == "overdue":
            stmt = stmt.where(Client.next_contact_at.is_not(None), Client.next_contact_at < now_utc)
        elif next_contact_mode == "week":
            stmt = stmt.where(Client.next_contact_at >= today_start, Client.next_contact_at <= week_end)
        elif next_contact_mode == "none":
            stmt = stmt.where(Client.next_contact_at.is_(None))

        active_task_exists = exists(
            select(Task.id).where(Task.client_id == Client.id, Task.status.in_((TaskStatus.OPEN, TaskStatus.IN_PROGRESS)))
        )
        done_task_exists = exists(select(Task.id).where(Task.client_id == Client.id, Task.status == TaskStatus.DONE))
        overdue_task_exists = exists(
            select(Task.id).where(
                Task.client_id == Client.id,
                Task.status.in_((TaskStatus.OPEN, TaskStatus.IN_PROGRESS)),
                Task.due_at.is_not(None),
                Task.due_at < today_start,
            )
        )
        today_task_exists = exists(
            select(Task.id).where(
                Task.client_id == Client.id,
                Task.status.in_((TaskStatus.OPEN, TaskStatus.IN_PROGRESS)),
                Task.due_at.is_not(None),
                Task.due_at >= today_start,
                Task.due_at < tomorrow_start,
            )
        )
        task_mode = filters.get("task_mode")
        if task_mode == "today":
            stmt = stmt.where(today_task_exists)
        elif task_mode == "overdue":
            stmt = stmt.where(overdue_task_exists)
        elif task_mode == "active":
            stmt = stmt.where(active_task_exists)
        elif task_mode == "none":
            stmt = stmt.where(~active_task_exists)
        elif task_mode == "done":
            stmt = stmt.where(done_task_exists)

        property_exists = exists(select(ClientProperty.id).where(ClientProperty.client_id == Client.id))
        object_mode = filters.get("object_mode")
        if object_mode == "has":
            stmt = stmt.where(property_exists)
        elif object_mode == "none":
            stmt = stmt.where(~property_exists)
        elif object_mode == "waiting_selection":
            stmt = stmt.where(
                Client.status.in_((ClientStatus.NEW, ClientStatus.IN_PROGRESS, ClientStatus.WAITING, ClientStatus.SHOWING)),
                ~property_exists,
            )

        sources = filters.get("sources") or []
        if sources:
            stmt = stmt.where(Client.source.in_(sources))

        search_query = (filters.get("search_query") or "").strip()
        if search_query:
            stmt = stmt.where(
                or_(
                    Client.full_name.ilike(f"%{search_query}%"),
                    Client.phone.ilike(f"%{search_query}%"),
                    Client.district.ilike(f"%{search_query}%"),
                    Client.source.ilike(f"%{search_query}%"),
                    Client.note.ilike(f"%{search_query}%"),
                )
            )
        return stmt

    def apply_client_sorting(self, *, stmt: Select[tuple[Client]], filters: dict) -> Select[tuple[Client]]:
        sort_mode = filters.get("sort") or "newest"
        now_utc = datetime.now(timezone.utc)
        if sort_mode == "oldest":
            return stmt.order_by(Client.created_at.asc())
        if sort_mode == "hot_first":
            return stmt.order_by(case((Client.status == ClientStatus.WAITING, 0), else_=1), Client.created_at.desc())
        if sort_mode == "next_contact":
            return stmt.order_by(Client.next_contact_at.asc().nullslast(), Client.created_at.desc())
        if sort_mode == "overdue_first":
            return stmt.order_by(
                case((and_(Client.next_contact_at.is_not(None), Client.next_contact_at < now_utc), 0), else_=1),
                Client.next_contact_at.asc().nullslast(),
            )
        if sort_mode == "budget_asc":
            return stmt.order_by(Client.budget.asc().nullslast(), Client.created_at.desc())
        if sort_mode == "budget_desc":
            return stmt.order_by(Client.budget.desc().nullslast(), Client.created_at.desc())
        if sort_mode == "name":
            return stmt.order_by(Client.full_name.asc(), Client.created_at.desc())
        return stmt.order_by(Client.created_at.desc())

    @staticmethod
    def _base_list_query() -> Select[tuple[Client]]:
        return select(Client).options(joinedload(Client.manager)).order_by(Client.created_at.desc())
