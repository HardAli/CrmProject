from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.dto.properties import CreatePropertyDTO
from app.common.enums import PropertyStatus, PropertyType, UserRole
from app.common.utils.property_search import build_property_search_conditions
from app.database.models.property import Property
from app.database.models.user import User
from app.services.object_filters import apply_object_filters


class PropertyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CreatePropertyDTO) -> Property:
        property_obj = Property(
            title=data.title,
            property_type=data.property_type,
            district=data.district,
            address=data.address,
            owner_phone=data.owner_phone,
            price=data.price,
            area=data.area,
            kitchen_area=data.kitchen_area,
            rooms=data.rooms,
            floor=data.floor,
            building_floors=data.building_floors,
            building_year=data.building_year,
            building_material=data.building_material,
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

    async def find_duplicate_candidates(
        self,
        *,
        owner_phone: str | None,
        property_type: PropertyType,
        address: str | None,
        rooms: int | None,
        limit: int = 50,
    ) -> Sequence[Property]:
        stmt = select(Property).options(joinedload(Property.manager)).where(Property.property_type == property_type)

        if owner_phone:
            stmt = stmt.where(Property.owner_phone == owner_phone)
        elif address:
            stmt = stmt.where(Property.address.ilike(f"%{address}%"))

        if rooms is not None:
            stmt = stmt.where(Property.rooms == rooms)

        stmt = stmt.order_by(Property.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def delete(self, property_obj: Property) -> None:
        await self._session.delete(property_obj)
        await self._session.flush()

    async def get_by_manager(self, manager_id: int, limit: int = 10, offset: int = 0) -> Sequence[Property]:
        stmt = self._base_list_query().where(Property.manager_id == manager_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_all(self, limit: int = 10, offset: int = 0) -> Sequence[Property]:
        stmt = self._base_list_query().limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_recent(self, limit: int = 10, manager_id: int | None = None) -> Sequence[Property]:
        stmt = self._base_list_query()
        if manager_id is not None:
            stmt = stmt.where(Property.manager_id == manager_id)
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_recent_global(self, limit: int = 10) -> Sequence[Property]:
        return await self.get_all(limit=limit, offset=0)

    async def get_visible_for_user(
        self,
        *,
        current_user: User,
        limit: int = 10,
        offset: int = 0,
    ) -> Sequence[Property]:
        if current_user.role == UserRole.MANAGER:
            return await self.get_by_manager(manager_id=current_user.id, limit=limit, offset=offset)

        return await self.get_all(limit=limit, offset=offset)

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
            search_text: str | None = None,
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
        available_fields = self.get_available_filter_fields()

        if manager_id is not None:
            stmt = stmt.where(Property.manager_id == manager_id)

        if search_text:
            search_conditions = build_property_search_conditions(search_text=search_text, available_fields=available_fields)
            if search_conditions:
                stmt = stmt.where(or_(*search_conditions))

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

    async def get_filtered_for_user(
        self,
        *,
        current_user: User,
        filters: dict[str, Any],
        limit: int,
        offset: int,
    ) -> Sequence[Property]:
        stmt = self._apply_user_scope(self._base_list_query_without_order(), current_user=current_user)
        stmt = apply_object_filters(stmt, filters, available_fields=self.get_available_filter_fields())
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count_filtered_for_user(self, *, current_user: User, filters: dict[str, Any]) -> int:
        stmt = self._apply_user_scope(select(Property.id), current_user=current_user)
        filtered_stmt = apply_object_filters(stmt, filters, available_fields=self.get_available_filter_fields())
        count_stmt = select(func.count()).select_from(filtered_stmt.order_by(None).subquery())
        result = await self._session.execute(count_stmt)
        return int(result.scalar_one() or 0)

    @staticmethod
    def get_available_filter_fields() -> set[str]:
        return set(Property.__table__.columns.keys())

    @staticmethod
    def _apply_user_scope(stmt: Select[Any], *, current_user: User) -> Select[Any]:
        if current_user.role == UserRole.MANAGER:
            return stmt.where(Property.manager_id == current_user.id)
        return stmt

    @staticmethod
    def _base_list_query_without_order() -> Select[tuple[Property]]:
        return select(Property).options(joinedload(Property.manager))

    @staticmethod
    def _base_list_query() -> Select[tuple[Property]]:
        return select(Property).options(joinedload(Property.manager)).order_by(Property.created_at.desc())
