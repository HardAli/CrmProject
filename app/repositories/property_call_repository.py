from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import PropertyStatus, UserRole
from app.database.models.property import Property
from app.database.models.property_call_log import PropertyCallLog
from app.database.models.user import User


class PropertyCallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_today_stats(self, *, manager_id: int, day_start: datetime, day_end: datetime) -> dict[str, int]:
        stmt = (
            select(PropertyCallLog.result, func.count(PropertyCallLog.id))
            .where(
                PropertyCallLog.manager_id == manager_id,
                PropertyCallLog.created_at >= day_start,
                PropertyCallLog.created_at < day_end,
            )
            .group_by(PropertyCallLog.result)
        )
        rows = (await self._session.execute(stmt)).all()
        return {str(result): int(count) for result, count in rows}

    async def create_log(
        self,
        *,
        property_id: int,
        manager_id: int | None,
        phone: str | None,
        result: str,
        reason: str | None = None,
        comment: str | None = None,
        next_call_at: datetime | None = None,
    ) -> PropertyCallLog:
        log = PropertyCallLog(
            property_id=property_id,
            manager_id=manager_id,
            phone=phone,
            result=result,
            reason=reason,
            comment=comment,
            next_call_at=next_call_at,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_property_for_call(self, *, current_user: User, property_id: int) -> Property | None:
        stmt = select(Property).where(Property.id == property_id)
        if current_user.role == UserRole.MANAGER:
            stmt = stmt.where(Property.manager_id == current_user.id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_queue_count(self, *, current_user: User, mode: str, exclude_ids: Sequence[int] | None) -> int:
        stmt = self._build_mode_stmt(current_user=current_user, mode=mode, exclude_ids=exclude_ids, count_only=True)
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_next_property(self, *, current_user: User, mode: str, exclude_ids: Sequence[int] | None) -> Property | None:
        stmt = self._build_mode_stmt(current_user=current_user, mode=mode, exclude_ids=exclude_ids, count_only=False)
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    def _build_mode_stmt(self, *, current_user: User, mode: str, exclude_ids: Sequence[int] | None, count_only: bool):
        now = datetime.now(timezone.utc)
        base_conditions = [
            Property.status == PropertyStatus.ACTIVE,
            Property.owner_phone.is_not(None),
            Property.owner_phone != "",
        ]

        if exclude_ids:
            base_conditions.append(~Property.id.in_(exclude_ids))

        if current_user.role == UserRole.MANAGER or mode == "my":
            base_conditions.append(Property.manager_id == current_user.id)

        if mode == "retry":
            base_conditions.extend(
                [
                    Property.last_call_status == "NO_ANSWER",
                    (Property.next_call_at.is_(None) | (Property.next_call_at <= now)),
                ]
            )
        elif mode == "new":
            base_conditions.append(Property.last_call_at.is_(None))

        if count_only:
            return select(func.count(Property.id)).where(*base_conditions)

        retry_due_expr = and_(
            Property.last_call_status == "NO_ANSWER",
            (Property.next_call_at.is_(None) | (Property.next_call_at <= now)),
        )

        return (
            select(Property)
            .where(*base_conditions)
            .order_by(
                case((Property.manager_id == current_user.id, 0), else_=1),
                case((Property.last_call_at.is_(None), 0), else_=1),
                case((retry_due_expr, 0), else_=1),
                Property.next_call_at.asc().nullsfirst(),
                Property.created_at.asc(),
            )
        )
