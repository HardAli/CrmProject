from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from app.common.enums import PropertyStatus
from app.common.utils.money import parse_money_to_tenge
from app.common.utils.phone_links import normalize_phone_digits
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.property_call_repository import PropertyCallRepository


class PropertyCallService:
    def __init__(self, repository: PropertyCallRepository) -> None:
        self._repository = repository

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
