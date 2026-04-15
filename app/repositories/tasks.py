from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time, timezone

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.enums import TaskStatus
from app.database.models.task import Task

ACTIVE_TASK_STATUSES: tuple[TaskStatus, ...] = (TaskStatus.OPEN, TaskStatus.IN_PROGRESS)


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        client_id: int,
        assigned_to: int,
        title: str,
        description: str | None,
        due_at: datetime,
        status: TaskStatus = TaskStatus.OPEN,
    ) -> Task:
        task = Task(
            client_id=client_id,
            assigned_to=assigned_to,
            title=title,
            description=description,
            due_at=due_at,
            status=status,
        )
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def get_my_tasks_for_date(
        self,
        *,
        user_id: int | None,
        target_date: date,
        limit: int = 20,
    ) -> Sequence[Task]:
        day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        stmt = self._base_query().where(
            Task.due_at.is_not(None),
            Task.due_at >= day_start,
            Task.due_at <= day_end,
            Task.status.in_(ACTIVE_TASK_STATUSES),
        )
        if user_id is not None:
            stmt = stmt.where(Task.assigned_to == user_id)

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_overdue_tasks(
        self,
        *,
        user_id: int | None,
        now_dt: datetime,
        limit: int = 20,
    ) -> Sequence[Task]:
        stmt = self._base_query().where(
            Task.due_at.is_not(None),
            Task.due_at < now_dt,
            Task.status.in_(ACTIVE_TASK_STATUSES),
        )
        if user_id is not None:
            stmt = stmt.where(Task.assigned_to == user_id)

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_client(self, *, client_id: int, limit: int = 20) -> Sequence[Task]:
        stmt = self._base_query().where(Task.client_id == client_id).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_assignee(self, *, assigned_to: int, limit: int = 20) -> Sequence[Task]:
        stmt = self._base_query().where(Task.assigned_to == assigned_to).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_all(self, *, limit: int = 20) -> Sequence[Task]:
        stmt = self._base_query().limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, task_id: int) -> Task | None:
        stmt = self._base_query().where(Task.id == task_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _base_query() -> Select[tuple[Task]]:
        return (
            select(Task)
            .options(
                joinedload(Task.client),
                joinedload(Task.assignee),
            )
            .order_by(Task.due_at.asc().nullslast(), Task.created_at.desc())
        )