from __future__ import annotations

from collections.abc import Sequence

from app.common.dto.properties import CreatePropertyDTO
from app.common.enums import UserRole
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.properties import PropertyRepository


class PropertyService:
    def __init__(self, property_repository: PropertyRepository) -> None:
        self._property_repository = property_repository

    async def create_property(self, current_user: User, data: CreatePropertyDTO) -> Property:
        if current_user.role == UserRole.SUPERVISOR:
            raise PermissionError("Роль supervisor не может создавать объекты")

        if current_user.role == UserRole.MANAGER and data.manager_id != current_user.id:
            raise PermissionError("Менеджер может создавать только свои объекты")

        return await self._property_repository.create(data)

    async def get_my_properties(self, current_user: User, limit: int = 10) -> Sequence[Property]:
        if current_user.role == UserRole.MANAGER:
            return await self._property_repository.get_by_manager(manager_id=current_user.id, limit=limit)
        return await self._property_repository.get_recent(limit=limit)

    async def get_recent_properties(self, current_user: User, limit: int = 10) -> Sequence[Property]:
        manager_id = current_user.id if current_user.role == UserRole.MANAGER else None
        return await self._property_repository.get_recent(limit=limit, manager_id=manager_id)

    async def get_property_for_view(self, current_user: User, property_id: int) -> Property | None:
        property_obj = await self._property_repository.get_by_id(property_id)
        if property_obj is None:
            return None

        if self.can_view_property(current_user=current_user, property_obj=property_obj):
            return property_obj

        return None

    @staticmethod
    def can_view_property(current_user: User, property_obj: Property) -> bool:
        if current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            return True
        return property_obj.manager_id == current_user.id

    @staticmethod
    def can_create_property(current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.MANAGER}