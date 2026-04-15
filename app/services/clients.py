from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from app.common.dto.clients import CreateClientDTO
from app.common.enums import ClientActionType, ClientStatus, UserRole
from app.database.models.client import Client
from app.database.models.client_log import ClientLog
from app.database.models.user import User
from app.repositories.client_logs import ClientLogRepository
from app.repositories.clients import ClientRepository


class ClientService:
    def __init__(self, client_repository: ClientRepository, client_log_repository: ClientLogRepository) -> None:
        self._client_repository = client_repository
        self._client_log_repository = client_log_repository

    async def create_client(self, data: CreateClientDTO) -> Client:
        client = await self._client_repository.create(data)
        await self._client_log_repository.create_log(
            client_id=client.id,
            user_id=data.manager_id,
            action_type=ClientActionType.CLIENT_CREATED,
            comment="Карточка клиента создана",
        )
        return client

    async def get_my_clients(self, current_user: User, limit: int = 10) -> Sequence[Client]:
        if current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            return await self._client_repository.get_recent(limit=limit)
        return await self._client_repository.get_by_manager(manager_id=current_user.id, limit=limit)

    async def get_clients_by_status(self, current_user: User, status: ClientStatus, limit: int = 10) -> Sequence[Client]:
        manager_id = None if self._can_view_all(current_user) else current_user.id
        return await self._client_repository.get_by_status(
            status=status,
            manager_id=manager_id,
            limit=limit,
        )

    async def get_recent_clients(self, current_user: User, limit: int = 10) -> Sequence[Client]:
        manager_id = None if self._can_view_all(current_user) else current_user.id
        return await self._client_repository.get_recent(limit=limit, manager_id=manager_id)

    async def get_client_for_view(self, current_user: User, client_id: int) -> Client | None:
        client = await self._client_repository.get_by_id(client_id)
        if client is None:
            return None

        if self.can_view_client(current_user, client):
            return client

        return None

    async def change_status(self, current_user: User, client_id: int, new_status: ClientStatus) -> Client:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")

        if not self.can_edit_client(current_user=current_user, client=client):
            raise PermissionError("Недостаточно прав для изменения статуса")

        old_status = client.status
        if old_status == new_status:
            return client

        updated_client = await self._client_repository.update_status(client=client, new_status=new_status)
        await self._client_log_repository.create_log(
            client_id=updated_client.id,
            user_id=current_user.id,
            action_type=ClientActionType.STATUS_CHANGED,
            comment=f'Статус: "{old_status.value}" → "{new_status.value}"',
        )
        return updated_client

    async def add_note(self, current_user: User, client_id: int, note: str) -> Client:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")

        if not self.can_edit_client(current_user=current_user, client=client):
            raise PermissionError("Недостаточно прав для добавления заметки")

        cleaned_note = note.strip()
        if not cleaned_note:
            raise ValueError("Заметка не должна быть пустой")

        updated_client = await self._client_repository.update_note(client=client, note=cleaned_note)
        await self._client_log_repository.create_log(
            client_id=updated_client.id,
            user_id=current_user.id,
            action_type=ClientActionType.NOTE_ADDED,
            comment=cleaned_note,
        )
        return updated_client

    async def get_client_history(self, current_user: User, client_id: int, limit: int = 10) -> Sequence[ClientLog]:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")

        return await self._client_log_repository.get_recent_by_client(client_id=client.id, limit=limit)

    async def update_next_contact(
            self,
            *,
            current_user: User,
            client_id: int,
            next_contact_at: datetime | None,
    ) -> Client:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")

        if not self.can_edit_client(current_user=current_user, client=client):
            raise PermissionError("Недостаточно прав для изменения следующего контакта")

        old_value = client.next_contact_at
        updated_client = await self._client_repository.update_next_contact(client=client,
                                                                           next_contact_at=next_contact_at)
        old_label = self._format_utc(old_value)
        new_label = self._format_utc(next_contact_at)

        await self._client_log_repository.create_log(
            client_id=updated_client.id,
            user_id=current_user.id,
            action_type=ClientActionType.NEXT_CONTACT_CHANGED,
            comment=f"{old_label} -> {new_label}",
        )
        return updated_client

    async def get_today_contacts(self, *, current_user: User, limit: int = 20) -> Sequence[Client]:
        manager_id = None if self._can_view_all(current_user) else current_user.id
        return await self._client_repository.get_contacts_for_date(
            manager_id=manager_id,
            target_date=datetime.now(tz=timezone.utc).date(),
            limit=limit,
        )

    async def get_overdue_contacts(self, *, current_user: User, limit: int = 20) -> Sequence[Client]:
        manager_id = None if self._can_view_all(current_user) else current_user.id
        return await self._client_repository.get_overdue_contacts(
            manager_id=manager_id,
            now_dt=datetime.now(tz=timezone.utc),
            limit=limit,
        )

    def can_edit_client(self, current_user: User, client: Client) -> bool:
        if current_user.role == UserRole.ADMIN:
            return True

        if current_user.role == UserRole.MANAGER:
            return client.manager_id == current_user.id

        return False

    def can_view_client(self, current_user: User, client: Client) -> bool:
        if self._can_view_all(current_user):
            return True
        return client.manager_id == current_user.id

    @staticmethod
    def _can_view_all(current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}

    async def _get_client_with_view_check(self, current_user: User, client_id: int) -> Client | None:
        client = await self._client_repository.get_by_id(client_id)
        if client is None:
            return None

        if not self.can_view_client(current_user=current_user, client=client):
            return None

        return client

    @staticmethod
    def _format_utc(value: datetime | None) -> str:
        if value is None:
            return "—"
        return value.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")