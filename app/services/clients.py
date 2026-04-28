from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal

from app.common.client_filters import normalize_filters
from app.common.dto.clients import CreateClientDTO
from app.common.dto.properties import CreatePropertyDTO
from app.common.enums import ClientActionType, ClientPropertyRelationStatus, ClientStatus, PropertyType, UserRole
from app.common.utils.phone_links import normalize_phone_digits
from app.database.models.client import Client
from app.database.models.client_log import ClientLog
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.client_logs import ClientLogRepository
from app.repositories.client_properties import ClientPropertyRepository
from app.repositories.clients import ClientRepository
from app.repositories.properties import PropertyRepository


class ClientService:
    def __init__(
        self,
        client_repository: ClientRepository,
        client_log_repository: ClientLogRepository,
        property_repository: PropertyRepository,
        client_property_repository: ClientPropertyRepository,
    ) -> None:
        self._client_repository = client_repository
        self._client_log_repository = client_log_repository
        self._property_repository = property_repository
        self._client_property_repository = client_property_repository

    async def create_client(self, data: CreateClientDTO) -> tuple[Client, int]:
        client, _, _ = await self.create_client_with_optional_property(
            current_user_id=data.manager_id,
            client_data=data,
            seller_property_data=None,
        )
        return client, 0

    async def create_client_with_optional_property(
        self,
        *,
        current_user_id: int,
        client_data: CreateClientDTO,
        seller_property_data: CreatePropertyDTO | None = None,
    ) -> tuple[Client, Property | None, bool]:
        client = await self._client_repository.create(client_data)
        await self._client_log_repository.create_log(
            client_id=client.id,
            user_id=current_user_id,
            action_type=ClientActionType.CLIENT_CREATED,
            comment="Карточка клиента создана",
        )
        if seller_property_data is None:
            return client, None, False

        existing_property = await self.find_existing_property_for_seller(
            owner_phone=seller_property_data.owner_phone,
            address=seller_property_data.address,
            property_type=seller_property_data.property_type,
            rooms=seller_property_data.rooms,
            area=seller_property_data.area,
            floor=seller_property_data.floor,
        )

        property_was_created = False
        property_obj = existing_property
        if property_obj is None:
            property_obj = await self._property_repository.create(seller_property_data)
            property_was_created = True

        await self._link_property_to_client(
            client_id=client.id,
            property_id=property_obj.id,
            user_id=current_user_id,
            property_title=property_obj.title,
        )
        return client, property_obj, property_was_created

    async def find_existing_property_for_seller(
        self,
        *,
        owner_phone: str | None,
        address: str | None,
        property_type: PropertyType,
        rooms: int | None,
        area: Decimal | None,
        floor: int | None,
    ) -> Property | None:
        candidates = await self._property_repository.find_duplicate_candidates(
            owner_phone=owner_phone,
            property_type=property_type,
            address=address,
            rooms=rooms,
        )
        target_phone = normalize_phone_digits(owner_phone)
        target_address = self._normalize_address(address)
        target_area = Decimal(area) if area is not None else None

        for candidate in candidates:
            if target_phone and normalize_phone_digits(candidate.owner_phone) != target_phone:
                continue
            if target_address:
                candidate_address = self._normalize_address(candidate.address)
                if candidate_address and candidate_address != target_address:
                    continue
            if rooms is not None and candidate.rooms is not None and candidate.rooms != rooms:
                continue
            if floor is not None and candidate.floor is not None and candidate.floor != floor:
                continue
            if target_area is not None and candidate.area is not None:
                if abs(Decimal(candidate.area) - target_area) > Decimal("1"):
                    continue
            return candidate
        return None

    async def _link_property_to_client(
        self,
        *,
        client_id: int,
        property_id: int,
        user_id: int,
        property_title: str,
    ) -> None:
        existing_link = await self._client_property_repository.get_existing(client_id=client_id, property_id=property_id)
        if existing_link is not None:
            return
        await self._client_property_repository.create(
            client_id=client_id,
            property_id=property_id,
            relation_status=ClientPropertyRelationStatus.SENT,
        )
        await self._client_log_repository.create_log(
            client_id=client_id,
            user_id=user_id,
            action_type=ClientActionType.PROPERTY_LINKED,
            comment=f'Объект #{property_id} "{property_title}" привязан к клиенту автоматически',
        )

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

    async def get_clients_filtered(
        self,
        *,
        current_user: User,
        filters: dict,
        per_page: int,
    ) -> tuple[list[Client], int, int]:
        manager_id = None if self._can_view_all(current_user) else current_user.id
        normalized = normalize_filters(filters)
        page = int(normalized.get("page") or 1)
        clients, total_count = await self._client_repository.get_filtered(
            filters=normalized,
            manager_id=manager_id,
            page=page,
            per_page=per_page,
        )
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        return clients, total_count, total_pages

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

    @staticmethod
    def _normalize_address(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = "".join(ch.lower() for ch in value.strip() if ch.isalnum())
        return normalized or None
