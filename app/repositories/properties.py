from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.dto.properties import CreatePropertyDTO
from app.common.enums import PropertyStatus, PropertyType, UserRole
from app.database.models.property import Property
from app.database.models.user import User


class PropertyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CreatePropertyDTO) -> Property:
        property_obj = Property(
            title=data.title,
            property_type=data.property_type,
            district=data.district,
            address=data.address,
            price=data.price,
            area=data.area,
            rooms=data.rooms,
            floor=data.floor,
            description=data.description,
            link=data.link,
            status=data.status,
            manager_id=data.manager_id,
        )
        self._session.add(property_obj)
        await self._session.flush()
        await self._session.refresh(property_obj)
        return property_obj

    async def get_by_id(self, property_id: int) -> Property | None:
        stmt = select(Property).options(joinedload(Property.manager)).where(Property.id == property_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_manager(self, manager_id: int, limit: int = 10, offset: int = 0) -> Sequence[Property]:
        stmt = self._base_list_query().where(Property.manager_id == manager_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_recent(self, limit: int = 10, manager_id: int | None = None) -> Sequence[Property]:
        stmt = self._base_list_query()
        if manager_id is not None:
            stmt = stmt.where(Property.manager_id == manager_id)
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_visible_for_user(
        self,
        *,
        current_user: User,
        limit: int = 10,
        offset: int = 0,
    ) -> Sequence[Property]:
        if current_user.role == UserRole.MANAGER:
            return await self.get_by_manager(manager_id=current_user.id, limit=limit, offset=offset)

        stmt = self._base_list_query().limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def exists_for_manager(self, property_id: int, manager_id: int) -> bool:
        stmt = select(Property.id).where(Property.id == property_id, Property.manager_id == manager_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_available_for_linking(
            self,
            *,
            current_user: User,
            limit: int = 10,
            exclude_property_ids: set[int] | None = None,
    ) -> Sequence[Property]:
        stmt = self._base_list_query()
        if current_user.role == UserRole.MANAGER:
            stmt = stmt.where(Property.manager_id == current_user.id)

        if exclude_property_ids:
            stmt = stmt.where(~Property.id.in_(exclude_property_ids))

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_properties(
            self,
            *,
            title: str | None = None,
            district: str | None = None,
            property_type: PropertyType | None = None,
            status: PropertyStatus | None = None,
            price_min: Decimal | None = None,
            price_max: Decimal | None = None,
            rooms: int | None = None,
            manager_id: int | None = None,
            limit: int = 10,
    ) -> Sequence[Property]:
        stmt = self._base_list_query()

        if manager_id is not None:
            stmt = stmt.where(Property.manager_id == manager_id)
        if title:
            stmt = stmt.where(Property.title.ilike(f"%{title}%"))
        if district:
            stmt = stmt.where(Property.district.ilike(f"%{district}%"))
        if property_type:
            stmt = stmt.where(Property.property_type == property_type)
        if status:
            stmt = stmt.where(Property.status == status)
        if price_min is not None:
            stmt = stmt.where(Property.price >= price_min)
        if price_max is not None:
            stmt = stmt.where(Property.price <= price_max)
        if rooms is not None:
            stmt = stmt.where(Property.rooms == rooms)

        result = await self._session.execute(stmt.limit(limit))
        return result.scalars().all()

    @staticmethod
    def _base_list_query() -> Select[tuple[Property]]:
        return select(Property).options(joinedload(Property.manager)).order_by(Property.created_at.desc())