from __future__ import annotations

from collections.abc import Sequence

from app.common.dto.clients import CreateClientDTO
from app.common.dto.properties import CreatePropertyDTO
from app.common.enums import ClientActionType, ClientPropertyRelationStatus, PropertyType, RequestType, UserRole
from app.common.utils.parsers import normalize_phone
from app.database.models.client import Client
from app.database.models.property import Property
from app.database.models.user import User
from app.common.utils.phone_links import normalize_owner_phone
from app.repositories.client_logs import ClientLogRepository
from app.repositories.client_properties import ClientPropertyRepository
from app.repositories.clients import ClientRepository
from app.repositories.properties import PropertyRepository


class PropertyService:
    def __init__(
            self,
            property_repository: PropertyRepository,
            client_repository: ClientRepository,
            client_property_repository: ClientPropertyRepository,
            client_log_repository: ClientLogRepository,
    ) -> None:
        self._property_repository = property_repository
        self._client_repository = client_repository
        self._client_property_repository = client_property_repository
        self._client_log_repository = client_log_repository

    async def create_property(self, current_user: User, data: CreatePropertyDTO) -> tuple[Property, int]:
        if current_user.role == UserRole.SUPERVISOR:
            raise PermissionError("Роль supervisor не может создавать объекты")

        if current_user.role == UserRole.MANAGER and data.manager_id != current_user.id:
            raise PermissionError("Менеджер может создавать только свои объекты")

        data.owner_phone = normalize_owner_phone(data.owner_phone)

        if data.floor is not None and data.floor < 0:
            raise ValueError("Этаж должен быть числом больше или равным 0.")

        if data.property_type == PropertyType.APARTMENT and data.building_floors is None:
            raise ValueError("Для квартиры необходимо указать этажность здания.")
        if data.building_floors is not None and data.building_floors <= 0:
            raise ValueError("Этажность здания должна быть положительным числом.")
        if data.floor is not None and data.building_floors is not None and data.floor > data.building_floors:
            raise ValueError("Этаж объекта не может быть больше этажности здания.")

        property_obj = await self._property_repository.create(data)
        linked_clients_count = 0
        return property_obj, linked_clients_count

    async def get_my_properties(self, current_user: User, limit: int = 10) -> Sequence[Property]:
        if current_user.role == UserRole.MANAGER:
            return await self._property_repository.get_by_manager(manager_id=current_user.id, limit=limit)
        return await self._property_repository.get_recent(limit=limit)

    async def get_recent_properties(self, current_user: User, limit: int = 10) -> Sequence[Property]:
        manager_id = current_user.id if current_user.role == UserRole.MANAGER else None
        return await self._property_repository.get_recent(limit=limit, manager_id=manager_id)

    async def get_global_properties(self, current_user: User, limit: int = 10) -> Sequence[Property]:
        if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.SUPERVISOR}:
            return []
        return await self._property_repository.get_all(limit=limit)

    async def get_recent_global_properties(self, current_user: User, limit: int = 10) -> Sequence[Property]:
        if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.SUPERVISOR}:
            return []
        return await self._property_repository.get_recent_global(limit=limit)

    async def get_property_for_view(self, current_user: User, property_id: int) -> Property | None:
        property_obj = await self._property_repository.get_by_id(property_id)
        if property_obj is None:
            return None

        if self.can_view_property(current_user=current_user, property_obj=property_obj):
            return property_obj

        return None

    @staticmethod
    def can_view_property(current_user: User, property_obj: Property) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.SUPERVISOR}

    @staticmethod
    def can_create_property(current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.MANAGER}

    @staticmethod
    def can_convert_property(*, current_user: User, property_obj: Property) -> bool:
        if current_user.role == UserRole.ADMIN:
            return True
        if current_user.role == UserRole.MANAGER:
            return property_obj.manager_id == current_user.id
        return False

    @staticmethod
    def can_delete_property(*, current_user: User, property_obj: Property) -> bool:
        if current_user.role == UserRole.ADMIN:
            return True
        if current_user.role == UserRole.MANAGER:
            return property_obj.manager_id == current_user.id
        return False

    async def convert_property_to_client(self, *, current_user: User, property_id: int) -> tuple[str, Client]:
        property_obj = await self._property_repository.get_by_id(property_id)
        if property_obj is None or not self.can_view_property(current_user=current_user, property_obj=property_obj):
            raise ValueError("Объект не найден или недоступен")

        if not self.can_convert_property(current_user=current_user, property_obj=property_obj):
            raise PermissionError("Недостаточно прав для создания клиента из этого объекта")

        owner_phone = (property_obj.owner_phone or "").strip()
        if not owner_phone:
            raise ValueError("Нельзя создать клиента без номера владельца")

        try:
            phone_normalized = normalize_phone(owner_phone)
        except ValueError as exc:
            raise ValueError("Нельзя создать клиента без корректного номера владельца") from exc
        existing_client = await self._client_repository.get_by_phone_normalized(phone_normalized)
        if existing_client is not None:
            existing_link = await self._client_property_repository.get_existing(
                client_id=existing_client.id,
                property_id=property_obj.id,
            )
            if existing_link is None:
                await self._client_property_repository.create(
                    client_id=existing_client.id,
                    property_id=property_obj.id,
                    relation_status=ClientPropertyRelationStatus.SENT,
                )
                await self._client_log_repository.create_log(
                    client_id=existing_client.id,
                    user_id=current_user.id,
                    action_type=ClientActionType.PROPERTY_LINKED,
                    comment=f'Объект #{property_obj.id} "{property_obj.title}" привязан к существующему клиенту',
                )
            return "existing", existing_client

        full_name = phone_normalized
        note = f"Клиент создан из объекта ID {property_obj.id}"
        manager_id = property_obj.manager_id if current_user.role == UserRole.ADMIN else current_user.id
        dto = CreateClientDTO(
            full_name=full_name,
            phone=phone_normalized,
            source="OBJECT_CONVERTED",
            request_type=RequestType.SELL,
            property_type=property_obj.property_type,
            district=property_obj.district,
            rooms=property_obj.rooms,
            budget=property_obj.price,
            floor=property_obj.floor,
            building_floors=property_obj.building_floors,
            wall_material=None,
            year_built=None,
            note=note,
            next_contact_at=None,
            manager_id=manager_id,
        )
        created_client = await self._client_repository.create(dto)
        await self._client_log_repository.create_log(
            client_id=created_client.id,
            user_id=current_user.id,
            action_type=ClientActionType.CLIENT_CREATED,
            comment=note,
        )
        await self._client_property_repository.create(
            client_id=created_client.id,
            property_id=property_obj.id,
            relation_status=ClientPropertyRelationStatus.SENT,
        )
        await self._client_log_repository.create_log(
            client_id=created_client.id,
            user_id=current_user.id,
            action_type=ClientActionType.PROPERTY_LINKED,
            comment=f'Связка client↔property создана автоматически с объектом #{property_obj.id}',
        )
        return "created", created_client

    async def delete_property(self, *, current_user: User, property_id: int) -> None:
        property_obj = await self._property_repository.get_by_id(property_id)
        if property_obj is None or not self.can_view_property(current_user=current_user, property_obj=property_obj):
            raise ValueError("Объект не найден или недоступен")

        if not self.can_delete_property(current_user=current_user, property_obj=property_obj):
            raise PermissionError("Недостаточно прав для удаления объекта")

        await self._client_property_repository.delete_by_property_id(property_obj.id)
        await self._property_repository.delete(property_obj)