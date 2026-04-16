from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum


class StatsPeriod(StrEnum):
    TODAY = "today"
    DAYS_30 = "30d"
    ALL_TIME = "all"


@dataclass(slots=True, frozen=True)
class PeriodBounds:
    start: datetime | None
    end: datetime


@dataclass(slots=True, frozen=True)
class ClientStatsDTO:
    total: int
    new: int
    in_progress: int
    waiting: int
    showing: int
    closed_success: int
    closed_failed: int
    contacts_today: int
    contacts_overdue: int


@dataclass(slots=True, frozen=True)
class TaskStatsDTO:
    open_total: int
    due_today: int
    overdue: int
    done: int
    in_progress: int


@dataclass(slots=True, frozen=True)
class PropertyStatsDTO:
    total: int
    active: int
    sold: int
    reserved: int
    archived: int


@dataclass(slots=True, frozen=True)
class ManagerStatsRowDTO:
    manager_id: int
    manager_name: str
    clients_total: int
    clients_new_period: int
    tasks_due_today: int
    tasks_overdue: int
    properties_active: int


@dataclass(slots=True, frozen=True)
class StatsBundleDTO:
    clients: ClientStatsDTO
    tasks: TaskStatsDTO
    properties: PropertyStatsDTO


def get_period_bounds(period: StatsPeriod) -> PeriodBounds:
    now = datetime.now(tz=timezone.utc)

    if period == StatsPeriod.ALL_TIME:
        return PeriodBounds(start=None, end=now)

    if period == StatsPeriod.TODAY:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return PeriodBounds(start=start, end=now)

    start = now - timedelta(days=30)
    return PeriodBounds(start=start, end=now)