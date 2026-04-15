from __future__ import annotations

from collections.abc import Sequence

from app.common.enums import ClientActionType, ClientPropertyRelationStatus, UserRole
from app.database.models.client import Client
from app.database.models.client_property import ClientProperty
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.client_logs import ClientLogRepository
from app.repositories.client_properties import ClientPropertyRepository
from app.repositories.clients import ClientRepository
from app.repositories.properties import PropertyRepository


class ClientPropertyService:
    def __init__(
        self,
        client_property_repository: ClientPropertyRepository,
        client_repository: ClientRepository,
        property_repository: PropertyRepository,
        client_log_repository: ClientLogRepository,
    ) -> None:
        self._client_property_repository = client_property_repository
        self._client_repository = client_repository
        self._property_repository = property_repository
        self._client_log_repository = client_log_repository

    async def link_property_to_client(self, *, current_user: User, client_id: int, property_id: int) -> ClientProperty:
        if current_user.role == UserRole.SUPERVISOR:
            raise PermissionError("У роли supervisor только чтение")

        client = await self._client_repository.get_by_id(client_id)
        if client is None or not self._can_view_client(current_user=current_user, client=client):
            raise ValueError("Клиент не найден или недоступен")

        property_obj = await self._property_repository.get_by_id(property_id)
        if property_obj is None or not self._can_view_property(current_user=current_user, property_obj=property_obj):
            raise ValueError("Объект не найден или недоступен")

        if not self.can_manage_client_property(current_user=current_user, client=client, property_obj=property_obj):
            raise PermissionError("Недостаточно прав для привязки объекта")

        existing = await self._client_property_repository.get_existing(client_id=client.id, property_id=property_obj.id)
        if existing is not None:
            return existing

        link = await self._client_property_repository.create(
            client_id=client.id,
            property_id=property_obj.id,
            relation_status=ClientPropertyRelationStatus.SENT,
        )
        loaded_link = await self._client_property_repository.get_by_id(link.id)
        if loaded_link is None:
            raise RuntimeError("Не удалось получить созданную связь")

        await self._client_log_repository.create_log(
            client_id=client.id,
            user_id=current_user.id,
            action_type=ClientActionType.PROPERTY_LINKED,
            comment=f'Объект #{property_obj.id} "{property_obj.title}" привязан к клиенту',
        )
        return loaded_link

    async def get_client_properties(self, *, current_user: User, client_id: int, limit: int = 10) -> Sequence[ClientProperty]:
        client = await self._client_repository.get_by_id(client_id)
        if client is None or not self._can_view_client(current_user=current_user, client=client):
            raise ValueError("Клиент не найден или недоступен")
        return await self._client_property_repository.get_by_client(client_id=client_id, limit=limit)

    async def get_client_property_link(self, *, current_user: User, link_id: int) -> ClientProperty:
        link = await self._client_property_repository.get_by_id(link_id)
        if link is None:
            raise ValueError("Связь не найдена")

        if not self._can_view_client_property(current_user=current_user, link=link):
            raise PermissionError("Нет прав на просмотр связи")

        return link

    async def get_existing(self, *, client_id: int, property_id: int) -> ClientProperty | None:
        return await self._client_property_repository.get_existing(client_id=client_id, property_id=property_id)

    async def change_relation_status(
        self,
        *,
        current_user: User,
        link_id: int,
        new_status: ClientPropertyRelationStatus,
    ) -> ClientProperty:
        link = await self.get_client_property_link(current_user=current_user, link_id=link_id)
        if current_user.role == UserRole.SUPERVISOR:
            raise PermissionError("У роли supervisor только чтение")

        if not self.can_manage_client_property(
            current_user=current_user,
            client=link.client,
            property_obj=link.property,
        ):
            raise PermissionError("Недостаточно прав для изменения статуса")

        old_status = link.relation_status
        if old_status == new_status:
            return link

        updated_link = await self._client_property_repository.update_relation_status(
            link=link,
            new_status=new_status,
        )
        await self._client_log_repository.create_log(
            client_id=updated_link.client_id,
            user_id=current_user.id,
            action_type=ClientActionType.PROPERTY_RELATION_STATUS_CHANGED,
            comment=f"Связь #{updated_link.id}: {old_status.value} -> {new_status.value}",
        )
        return updated_link

    async def get_available_properties_for_linking(
        self,
        *,
        current_user: User,
        client_id: int,
        limit: int = 10,
    ) -> Sequence[Property]:
        client = await self._client_repository.get_by_id(client_id)
        if client is None or not self._can_view_client(current_user=current_user, client=client):
            raise ValueError("Клиент не найден или недоступен")

        linked = await self._client_property_repository.get_by_client(client_id=client_id, limit=1000)
        exclude_property_ids = {item.property_id for item in linked}
        return await self._property_repository.get_available_for_linking(
            current_user=current_user,
            limit=limit,
            exclude_property_ids=exclude_property_ids,
        )

    async def can_link_properties_to_client(self, *, current_user: User, client_id: int) -> bool:
        client = await self._client_repository.get_by_id(client_id)
        if client is None:
            return False
        return self.can_link_for_client(current_user=current_user, client=client)

    def can_manage_client_property(
        self,
        *,
        current_user: User,
        client: Client,
        property_obj: Property,
    ) -> bool:
        if current_user.role == UserRole.ADMIN:
            return True
        if current_user.role == UserRole.MANAGER:
            return client.manager_id == current_user.id and property_obj.manager_id == current_user.id
        return False

    def can_link_for_client(self, *, current_user: User, client: Client) -> bool:
        if current_user.role == UserRole.ADMIN:
            return True
        if current_user.role == UserRole.MANAGER:
            return client.manager_id == current_user.id
        return False

    def _can_view_client_property(self, *, current_user: User, link: ClientProperty) -> bool:
        if current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            return True
        return link.client.manager_id == current_user.id and link.property.manager_id == current_user.id

    @staticmethod
    def _can_view_client(*, current_user: User, client: Client) -> bool:
        if current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            return True
        return client.manager_id == current_user.id

    @staticmethod
    def _can_view_property(*, current_user: User, property_obj: Property) -> bool:
        if current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            return True
        return property_obj.manager_id == current_user.id