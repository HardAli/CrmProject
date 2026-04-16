from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dto.statistics import (
    ClientStatsDTO,
    ManagerStatsRowDTO,
    PeriodBounds,
    PropertyStatsDTO,
    TaskStatsDTO,
)
from app.common.enums import ClientStatus, PropertyStatus, TaskStatus, UserRole
from app.database.models.client import Client
from app.database.models.property import Property
from app.database.models.task import Task
from app.database.models.user import User

ACTIVE_TASK_STATUSES: tuple[TaskStatus, ...] = (TaskStatus.OPEN, TaskStatus.IN_PROGRESS)


class StatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_client_stats(self, *, manager_id: int | None, period: PeriodBounds) -> ClientStatsDTO:
        now = datetime.now(tz=timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        stmt = select(
            func.count(Client.id),
            func.count(case((Client.created_at >= period.start, 1))) if period.start else func.count(Client.id),
            func.count(case((Client.status == ClientStatus.IN_PROGRESS, 1))),
            func.count(case((Client.status == ClientStatus.WAITING, 1))),
            func.count(case((Client.status == ClientStatus.SHOWING, 1))),
            func.count(case((Client.status == ClientStatus.CLOSED_SUCCESS, 1))),
            func.count(case((Client.status == ClientStatus.CLOSED_FAILED, 1))),
            func.count(
                case(
                    (
                        (Client.next_contact_at.is_not(None))
                        & (Client.next_contact_at >= day_start)
                        & (Client.next_contact_at <= day_end),
                        1,
                    )
                )
            ),
            func.count(case(((Client.next_contact_at.is_not(None)) & (Client.next_contact_at < now), 1))),
        )

        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)

        if period.start is not None:
            stmt = stmt.where(Client.created_at >= period.start, Client.created_at <= period.end)

        row = (await self._session.execute(stmt)).one()
        return ClientStatsDTO(
            total=int(row[0] or 0),
            new=int(row[1] or 0),
            in_progress=int(row[2] or 0),
            waiting=int(row[3] or 0),
            showing=int(row[4] or 0),
            closed_success=int(row[5] or 0),
            closed_failed=int(row[6] or 0),
            contacts_today=int(row[7] or 0),
            contacts_overdue=int(row[8] or 0),
        )

    async def get_task_stats(self, *, manager_id: int | None, period: PeriodBounds) -> TaskStatsDTO:
        now = datetime.now(tz=timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        stmt = select(
            func.count(case((Task.status.in_(ACTIVE_TASK_STATUSES), 1))),
            func.count(
                case(
                    (
                        (Task.due_at.is_not(None))
                        & (Task.due_at >= day_start)
                        & (Task.due_at <= day_end)
                        & (Task.status.in_(ACTIVE_TASK_STATUSES)),
                        1,
                    )
                )
            ),
            func.count(
                case(
                    (
                        (Task.due_at.is_not(None))
                        & (Task.due_at < now)
                        & (Task.status.in_(ACTIVE_TASK_STATUSES)),
                        1,
                    )
                )
            ),
            func.count(case((Task.status == TaskStatus.DONE, 1))),
            func.count(case((Task.status == TaskStatus.IN_PROGRESS, 1))),
        )

        if manager_id is not None:
            stmt = stmt.where(Task.assigned_to == manager_id)

        if period.start is not None:
            stmt = stmt.where(Task.created_at >= period.start, Task.created_at <= period.end)

        row = (await self._session.execute(stmt)).one()
        return TaskStatsDTO(
            open_total=int(row[0] or 0),
            due_today=int(row[1] or 0),
            overdue=int(row[2] or 0),
            done=int(row[3] or 0),
            in_progress=int(row[4] or 0),
        )

    async def get_property_stats(self, *, manager_id: int | None, period: PeriodBounds) -> PropertyStatsDTO:
        stmt = select(
            func.count(Property.id),
            func.count(case((Property.status == PropertyStatus.ACTIVE, 1))),
            func.count(case((Property.status == PropertyStatus.SOLD, 1))),
            func.count(case((Property.status == PropertyStatus.RESERVED, 1))),
            func.count(case((Property.status == PropertyStatus.ARCHIVED, 1))),
        )

        if manager_id is not None:
            stmt = stmt.where(Property.manager_id == manager_id)

        if period.start is not None:
            stmt = stmt.where(Property.created_at >= period.start, Property.created_at <= period.end)

        row = (await self._session.execute(stmt)).one()
        return PropertyStatsDTO(
            total=int(row[0] or 0),
            active=int(row[1] or 0),
            sold=int(row[2] or 0),
            reserved=int(row[3] or 0),
            archived=int(row[4] or 0),
        )

    async def get_lead_source_stats(self, *, manager_id: int | None, period: PeriodBounds) -> dict[str, int]:
        stmt = (
            select(Client.source, func.count(Client.id))
            .group_by(Client.source)
            .order_by(func.count(Client.id).desc(), Client.source.asc())
        )

        if manager_id is not None:
            stmt = stmt.where(Client.manager_id == manager_id)

        if period.start is not None:
            stmt = stmt.where(Client.created_at >= period.start, Client.created_at <= period.end)

        rows = (await self._session.execute(stmt)).all()
        result: dict[str, int] = {}
        for source, count in rows:
            result[(source or "Не указан")] = int(count or 0)
        return result

    async def get_manager_stats(self, *, period: PeriodBounds) -> Sequence[ManagerStatsRowDTO]:
        now = datetime.now(tz=timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        clients_total_subq = (
            select(Client.manager_id.label("manager_id"), func.count(Client.id).label("clients_total"))
            .group_by(Client.manager_id)
            .subquery()
        )

        clients_new_subq = select(Client.manager_id.label("manager_id"), func.count(Client.id).label("clients_new"))
        if period.start is not None:
            clients_new_subq = clients_new_subq.where(Client.created_at >= period.start, Client.created_at <= period.end)
        clients_new_subq = clients_new_subq.group_by(Client.manager_id).subquery()

        tasks_today_subq = (
            select(Task.assigned_to.label("manager_id"), func.count(Task.id).label("tasks_today"))
            .where(
                Task.due_at.is_not(None),
                Task.due_at >= day_start,
                Task.due_at <= day_end,
                Task.status.in_(ACTIVE_TASK_STATUSES),
            )
            .group_by(Task.assigned_to)
            .subquery()
        )

        tasks_overdue_subq = (
            select(Task.assigned_to.label("manager_id"), func.count(Task.id).label("tasks_overdue"))
            .where(
                Task.due_at.is_not(None),
                Task.due_at < now,
                Task.status.in_(ACTIVE_TASK_STATUSES),
            )
            .group_by(Task.assigned_to)
            .subquery()
        )

        properties_active_subq = (
            select(Property.manager_id.label("manager_id"), func.count(Property.id).label("properties_active"))
            .where(Property.status == PropertyStatus.ACTIVE)
            .group_by(Property.manager_id)
            .subquery()
        )

        stmt = (
            select(
                User.id,
                User.full_name,
                func.coalesce(clients_total_subq.c.clients_total, 0),
                func.coalesce(clients_new_subq.c.clients_new, 0),
                func.coalesce(tasks_today_subq.c.tasks_today, 0),
                func.coalesce(tasks_overdue_subq.c.tasks_overdue, 0),
                func.coalesce(properties_active_subq.c.properties_active, 0),
            )
            .outerjoin(clients_total_subq, clients_total_subq.c.manager_id == User.id)
            .outerjoin(clients_new_subq, clients_new_subq.c.manager_id == User.id)
            .outerjoin(tasks_today_subq, tasks_today_subq.c.manager_id == User.id)
            .outerjoin(tasks_overdue_subq, tasks_overdue_subq.c.manager_id == User.id)
            .outerjoin(properties_active_subq, properties_active_subq.c.manager_id == User.id)
            .where(User.role == UserRole.MANAGER, User.is_active.is_(True))
            .order_by(User.full_name.asc())
        )

        rows = (await self._session.execute(stmt)).all()
        return [
            ManagerStatsRowDTO(
                manager_id=int(row[0]),
                manager_name=str(row[1]),
                clients_total=int(row[2] or 0),
                clients_new_period=int(row[3] or 0),
                tasks_due_today=int(row[4] or 0),
                tasks_overdue=int(row[5] or 0),
                properties_active=int(row[6] or 0),
            )
            for row in rows
        ]