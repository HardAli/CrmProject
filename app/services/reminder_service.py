from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from app.database.models.client import Client
from app.database.models.task import Task
from app.database.models.user import User
from app.repositories.clients import ClientRepository
from app.repositories.tasks import TaskRepository

REMINDER_LIST_LIMIT = 10


@dataclass(slots=True)
class DailySummary:
    today_tasks_count: int
    overdue_tasks_count: int
    today_contacts_count: int
    overdue_contacts_count: int
    today_tasks: list[Task]
    overdue_tasks: list[Task]
    today_contacts: list[Client]

    @property
    def has_data(self) -> bool:
        return any(
            (
                self.today_tasks_count,
                self.overdue_tasks_count,
                self.today_contacts_count,
                self.overdue_contacts_count,
            )
        )


class ReminderService:
    def __init__(self, task_repository: TaskRepository, client_repository: ClientRepository) -> None:
        self._task_repository = task_repository
        self._client_repository = client_repository

    async def build_daily_summary_for_user(self, user: User, target_date: date | None = None) -> DailySummary:
        now_dt = datetime.now(tz=timezone.utc)
        effective_date = target_date or now_dt.date()

        today_tasks = await self.collect_today_tasks(user=user, target_date=effective_date)
        overdue_tasks = await self.collect_overdue_tasks(user=user, now_dt=now_dt)
        today_contacts = await self.collect_today_contacts(user=user, target_date=effective_date)
        overdue_contacts = await self.collect_overdue_contacts(user=user, now_dt=now_dt)

        return DailySummary(
            today_tasks_count=len(today_tasks),
            overdue_tasks_count=len(overdue_tasks),
            today_contacts_count=len(today_contacts),
            overdue_contacts_count=len(overdue_contacts),
            today_tasks=today_tasks,
            overdue_tasks=overdue_tasks,
            today_contacts=today_contacts,
        )

    async def collect_today_tasks(self, *, user: User, target_date: date) -> list[Task]:
        return list(
            await self._task_repository.get_today_tasks_for_user(
                user_id=user.id,
                target_date=target_date,
                limit=REMINDER_LIST_LIMIT,
            )
        )

    async def collect_overdue_tasks(self, *, user: User, now_dt: datetime) -> list[Task]:
        return list(
            await self._task_repository.get_overdue_tasks_for_user(
                user_id=user.id,
                now_dt=now_dt,
                limit=REMINDER_LIST_LIMIT,
            )
        )

    async def collect_today_contacts(self, *, user: User, target_date: date) -> list[Client]:
        return list(
            await self._client_repository.get_today_contacts_for_user(
                user_id=user.id,
                target_date=target_date,
                limit=REMINDER_LIST_LIMIT,
            )
        )

    async def collect_overdue_contacts(self, *, user: User, now_dt: datetime) -> list[Client]:
        return list(
            await self._client_repository.get_overdue_contacts_for_user(
                user_id=user.id,
                now_dt=now_dt,
                limit=REMINDER_LIST_LIMIT,
            )
        )

    async def collect_upcoming_tasks(self, *, user: User, now_dt: datetime, horizon_minutes: int) -> list[Task]:
        return list(
            await self._task_repository.get_upcoming_tasks_for_user(
                user_id=user.id,
                now_dt=now_dt,
                horizon_minutes=horizon_minutes,
                limit=REMINDER_LIST_LIMIT,
            )
        )