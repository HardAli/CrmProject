from __future__ import annotations

from collections.abc import Sequence

from app.common.dto.statistics import ManagerStatsRowDTO, StatsBundleDTO, StatsPeriod, get_period_bounds
from app.common.enums import UserRole
from app.database.models.user import User
from app.repositories.statistics import StatisticsRepository


class StatisticsService:
    def __init__(self, statistics_repository: StatisticsRepository) -> None:
        self._statistics_repository = statistics_repository

    async def get_personal_stats(self, *, current_user: User, period: StatsPeriod) -> StatsBundleDTO:
        self._ensure_active_user(current_user)
        bounds = get_period_bounds(period)

        clients = await self._statistics_repository.get_client_stats(manager_id=current_user.id, period=bounds)
        tasks = await self._statistics_repository.get_task_stats(manager_id=current_user.id, period=bounds)
        properties = await self._statistics_repository.get_property_stats(manager_id=current_user.id, period=bounds)
        return StatsBundleDTO(clients=clients, tasks=tasks, properties=properties)

    async def get_global_stats(self, *, current_user: User, period: StatsPeriod) -> StatsBundleDTO:
        self._ensure_active_user(current_user)
        if current_user.role not in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            raise PermissionError("Недостаточно прав для просмотра общей статистики")

        bounds = get_period_bounds(period)
        clients = await self._statistics_repository.get_client_stats(manager_id=None, period=bounds)
        tasks = await self._statistics_repository.get_task_stats(manager_id=None, period=bounds)
        properties = await self._statistics_repository.get_property_stats(manager_id=None, period=bounds)
        return StatsBundleDTO(clients=clients, tasks=tasks, properties=properties)

    async def get_manager_stats(self, *, current_user: User, period: StatsPeriod) -> Sequence[ManagerStatsRowDTO]:
        self._ensure_active_user(current_user)
        if current_user.role not in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            raise PermissionError("Недостаточно прав для просмотра статистики по менеджерам")

        bounds = get_period_bounds(period)
        return await self._statistics_repository.get_manager_stats(period=bounds)

    async def get_lead_source_stats(self, *, current_user: User, period: StatsPeriod) -> dict[str, int]:
        self._ensure_active_user(current_user)
        bounds = get_period_bounds(period)

        manager_id = current_user.id if current_user.role == UserRole.MANAGER else None
        return await self._statistics_repository.get_lead_source_stats(manager_id=manager_id, period=bounds)

    @staticmethod
    def _ensure_active_user(current_user: User) -> None:
        if not current_user.is_active:
            raise PermissionError("Пользователь деактивирован")