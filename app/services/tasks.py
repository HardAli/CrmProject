from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from app.common.enums import ClientActionType, UserRole
from app.database.models.task import Task
from app.database.models.user import User
from app.repositories.client_logs import ClientLogRepository
from app.repositories.clients import ClientRepository
from app.repositories.tasks import TaskRepository

DEFAULT_TASK_LIMIT = 20


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        client_repository: ClientRepository,
        client_log_repository: ClientLogRepository,
    ) -> None:
        self._task_repository = task_repository
        self._client_repository = client_repository
        self._client_log_repository = client_log_repository

    async def create_task(
        self,
        *,
        current_user: User,
        client_id: int,
        title: str,
        description: str | None,
        due_at: datetime,
    ) -> Task:
        client = await self._client_repository.get_by_id(client_id)
        if client is None:
            raise ValueError("Клиент не найден")

        if current_user.role == UserRole.SUPERVISOR:
            raise PermissionError("Супервайзер не может создавать задачи")

        if current_user.role == UserRole.MANAGER and client.manager_id != current_user.id:
            raise PermissionError("Менеджер может создавать задачи только по своим клиентам")

        title_cleaned = title.strip()
        if not title_cleaned:
            raise ValueError("Заголовок задачи не должен быть пустым")

        description_cleaned = (description or "").strip() or None
        task = await self._task_repository.create(
            client_id=client.id,
            assigned_to=current_user.id,
            title=title_cleaned,
            description=description_cleaned,
            due_at=due_at,
        )

        due_label = due_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
        await self._client_log_repository.create_log(
            client_id=client.id,
            user_id=current_user.id,
            action_type=ClientActionType.TASK_CREATED,
            comment=f"Задача: {title_cleaned}. Срок: {due_label}",
        )
        created_task = await self._task_repository.get_by_id(task.id)
        if created_task is None:
            raise RuntimeError("Не удалось загрузить созданную задачу")
        return created_task

    async def get_today_tasks(self, *, current_user: User, limit: int = DEFAULT_TASK_LIMIT) -> Sequence[Task]:
        user_id = None if self._can_view_all(current_user) else current_user.id
        return await self._task_repository.get_my_tasks_for_date(
            user_id=user_id,
            target_date=datetime.now(tz=timezone.utc).date(),
            limit=limit,
        )

    async def get_overdue_tasks(self, *, current_user: User, limit: int = DEFAULT_TASK_LIMIT) -> Sequence[Task]:
        user_id = None if self._can_view_all(current_user) else current_user.id
        return await self._task_repository.get_overdue_tasks(
            user_id=user_id,
            now_dt=datetime.now(tz=timezone.utc),
            limit=limit,
        )

    async def get_my_tasks(self, *, current_user: User, limit: int = DEFAULT_TASK_LIMIT) -> Sequence[Task]:
        if self._can_view_all(current_user):
            return await self._task_repository.get_all(limit=limit)
        return await self._task_repository.get_by_assignee(assigned_to=current_user.id, limit=limit)

    @staticmethod
    def _can_view_all(current_user: User) -> bool:
        return current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}