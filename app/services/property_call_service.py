from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from app.common.enums import PropertyStatus
from app.common.dto.clients import CreateClientDTO
from app.common.utils.money import parse_money_to_tenge
from app.common.utils.phone_links import normalize_phone_digits
from app.common.utils.parsers import normalize_phone
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.client_logs import ClientLogRepository
from app.repositories.client_properties import ClientPropertyRepository
from app.repositories.clients import ClientRepository
from app.repositories.property_call_repository import PropertyCallRepository
from app.common.enums import ClientActionType, ClientPropertyRelationStatus, PropertyType, RequestType, UserRole


class PropertyCallService:
    def __init__(self, repository: PropertyCallRepository, client_repository: ClientRepository, client_property_repository: ClientPropertyRepository, client_log_repository: ClientLogRepository) -> None:
        self._repository = repository
        self._client_repository = client_repository
        self._client_property_repository = client_property_repository
        self._client_log_repository = client_log_repository

    async def get_call_menu_stats(self, current_user: User) -> dict[str, int]:
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        stats = await self._repository.get_today_stats(
            manager_id=current_user.id,
            day_start=day_start,
            day_end=day_end,
        )
        return {
            "AGREED": stats.get("AGREED", 0),
            "NO_ANSWER": stats.get("NO_ANSWER", 0),
            "REJECTED": stats.get("REJECTED", 0),
            "SOLD": stats.get("SOLD", 0),
            "SKIPPED": stats.get("SKIPPED", 0),
        }

    async def get_next_property_for_call(
        self,
        current_user: User,
        mode: str,
        exclude_ids: list[int] | None = None,
    ) -> Property | None:
        return await self._repository.get_next_property(current_user=current_user, mode=mode, exclude_ids=exclude_ids)

    async def get_call_queue_count(
        self,
        current_user: User,
        mode: str,
        exclude_ids: list[int] | None = None,
    ) -> int:
        return await self._repository.get_queue_count(current_user=current_user, mode=mode, exclude_ids=exclude_ids)

    async def save_call_result(
        self,
        property_id: int,
        current_user: User,
        result: str,
        reason: str | None = None,
        comment: str | None = None,
        next_call_at: datetime | None = None,
    ) -> None:
        property_obj = await self._repository.get_property_for_call(current_user=current_user, property_id=property_id)
        if property_obj is None:
            raise ValueError("Объект не найден")

        await self._repository.create_log(
            property_id=property_id,
            manager_id=current_user.id,
            phone=normalize_phone_digits(property_obj.owner_phone),
            result=result,
            reason=reason,
            comment=comment,
            next_call_at=next_call_at,
        )

        if result == "SKIPPED":
            return

        now = datetime.now(timezone.utc)
        property_obj.last_call_status = result
        property_obj.last_call_at = now
        property_obj.next_call_at = next_call_at
        property_obj.call_attempts = int(property_obj.call_attempts or 0) + 1

        if result == "SOLD":
            property_obj.status = PropertyStatus.SOLD

    async def apply_not_reached(self, *, property_id: int, current_user: User, next_call_at: datetime | None = None) -> None:
        property_obj = await self._repository.get_property_for_call(current_user=current_user, property_id=property_id)
        if property_obj is None:
            raise ValueError("Объект не найден")
        await self.save_call_result(property_id=property_id, current_user=current_user, result="NO_ANSWER", next_call_at=next_call_at)
        property_obj.status = PropertyStatus.NOT_REACHED
        property_obj.needs_recall = True

    async def apply_refused(self, *, property_id: int, current_user: User) -> None:
        if current_user.role == UserRole.SUPERVISOR:
            raise PermissionError("У роли supervisor только чтение")
        property_obj = await self._repository.get_property_for_call(current_user=current_user, property_id=property_id)
        if property_obj is None:
            raise ValueError("Объект не найден")
        manager_name = self.get_current_manager_name(current_user)
        property_obj.refused_manager_names = self.build_refusal_managers(property_obj.refused_manager_names, manager_name)
        property_obj.status = PropertyStatus.REFUSED_TO_WORK
        property_obj.needs_recall = False
        await self.save_call_result(property_id=property_id, current_user=current_user, result="REJECTED", reason="NO_COOPERATION")

    async def apply_agreed(self, *, property_id: int, current_user: User) -> tuple[str, int]:
        property_obj = await self._repository.get_property_for_call(current_user=current_user, property_id=property_id)
        if property_obj is None:
            raise ValueError("Объект не найден")
        await self.save_call_result(property_id=property_id, current_user=current_user, result="AGREED")
        property_obj.status = PropertyStatus.AGREED
        property_obj.needs_recall = False

        phone_normalized = normalize_phone(property_obj.owner_phone)
        existing_client = await self._client_repository.get_by_phone_normalized(phone_normalized)
        if existing_client is not None:
            link = await self._client_property_repository.get_existing(client_id=existing_client.id, property_id=property_obj.id)
            if link is None:
                await self._client_property_repository.create(client_id=existing_client.id, property_id=property_obj.id, relation_status=ClientPropertyRelationStatus.SENT)
                await self._client_log_repository.create_log(client_id=existing_client.id, user_id=current_user.id, action_type=ClientActionType.PROPERTY_LINKED, comment=f'Объект #{property_obj.id} "{property_obj.title}" привязан после прозвона')
            return "existing", existing_client.id

        dto = CreateClientDTO(
            full_name=phone_normalized,
            phone=phone_normalized,
            source="CALL_AGREED",
            request_type=RequestType.SELL,
            property_type=property_obj.property_type if isinstance(property_obj.property_type, PropertyType) else PropertyType.APARTMENT,
            district=property_obj.district,
            rooms=str(property_obj.rooms) if property_obj.rooms is not None else None,
            budget=property_obj.price,
            floor=property_obj.floor,
            building_floors=property_obj.building_floors,
            wall_material=None,
            year_built=property_obj.building_year,
            note=f"Создан из прозвона по объекту #{property_obj.id}",
            next_contact_at=None,
            manager_id=property_obj.manager_id,
        )
        created = await self._client_repository.create(dto)
        await self._client_log_repository.create_log(client_id=created.id, user_id=current_user.id, action_type=ClientActionType.CLIENT_CREATED, comment="Клиент создан из прозвона")
        await self._client_property_repository.create(client_id=created.id, property_id=property_obj.id, relation_status=ClientPropertyRelationStatus.SENT)
        return "created", created.id

    @staticmethod
    def get_current_manager_name(current_user: User) -> str:
        full_name = (current_user.full_name or "").strip()
        if full_name:
            return full_name
        return f"manager#{current_user.id}"

    @staticmethod
    def build_refusal_managers(existing_value: str | None, current_manager_name: str) -> str:
        names = [item.strip() for item in (existing_value or "").split(",") if item.strip()]
        normalized_existing = {name.casefold() for name in names}
        candidate = current_manager_name.strip()
        if candidate and candidate.casefold() not in normalized_existing:
            names.append(candidate)
        return ", ".join(names)

    async def add_call_note(self, property_id: int, current_user: User, note: str) -> None:
        property_obj = await self._repository.get_property_for_call(current_user=current_user, property_id=property_id)
        if property_obj is None:
            raise ValueError("Объект не найден")
        await self._repository.create_log(
            property_id=property_id,
            manager_id=current_user.id,
            phone=normalize_phone_digits(property_obj.owner_phone),
            result="NOTE",
            comment=note,
        )

    async def update_property_price_from_call(self, property_id: int, current_user: User, price: Decimal) -> tuple[Decimal, Decimal]:
        property_obj = await self._repository.get_property_for_call(current_user=current_user, property_id=property_id)
        if property_obj is None:
            raise ValueError("Объект не найден")

        old_price = property_obj.price
        property_obj.price = price
        await self._repository.create_log(
            property_id=property_id,
            manager_id=current_user.id,
            phone=normalize_phone_digits(property_obj.owner_phone),
            result="PRICE_UPDATED",
            comment=f"Цена изменена: {old_price} -> {price}",
        )
        return old_price, price

    async def mark_property_sold_from_call(self, property_id: int, current_user: User) -> None:
        await self.save_call_result(property_id=property_id, current_user=current_user, result="SOLD", reason="SOLD")

    @staticmethod
    def calc_no_answer_next_call(option: str) -> datetime | None:
        now = datetime.now(timezone.utc)
        if option == "2h":
            return now + timedelta(hours=2)
        if option == "evening":
            evening = now.replace(hour=18, minute=0, second=0, microsecond=0)
            if now >= evening:
                evening += timedelta(days=1)
            return evening
        if option == "tomorrow":
            tomorrow = now + timedelta(days=1)
            return datetime.combine(tomorrow.date(), time(10, 0), tzinfo=timezone.utc)
        if option == "3d":
            in_3_days = now + timedelta(days=3)
            return datetime.combine(in_3_days.date(), time(10, 0), tzinfo=timezone.utc)
        return None

    @staticmethod
    def parse_price_value(raw_value: str) -> Decimal | None:
        return parse_money_to_tenge(raw_value)
