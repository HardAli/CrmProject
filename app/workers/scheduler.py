from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.database.session import async_session_factory
from app.repositories.clients import ClientRepository
from app.repositories.tasks import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService
from app.services.reminder_service import ReminderService
from app.workers.reminder_sender import ReminderSender

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(
        self,
        *,
        bot: Bot,
        daily_summary_hour_utc: int = 7,
        frequent_check_minutes: int = 15,
        upcoming_task_horizon_minutes: int = 30,
    ) -> None:
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._sender = ReminderSender(bot=bot, notification_service=NotificationService())
        self._daily_summary_hour_utc = daily_summary_hour_utc
        self._frequent_check_minutes = frequent_check_minutes
        self._upcoming_task_horizon_minutes = upcoming_task_horizon_minutes

    def start(self) -> None:
        self._scheduler.add_job(
            self._run_daily_summary_job,
            trigger=CronTrigger(hour=self._daily_summary_hour_utc, minute=0),
            id="daily_summary_job",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        self._scheduler.add_job(
            self._run_frequent_reminders_job,
            trigger=IntervalTrigger(minutes=self._frequent_check_minutes),
            id="frequent_reminders_job",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        self._scheduler.start()
        logger.info("Reminder scheduler started")

    async def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Reminder scheduler stopped")

    async def _run_daily_summary_job(self) -> None:
        await self._run_in_session(self._dispatch_daily_summary)

    async def _run_frequent_reminders_job(self) -> None:
        await self._run_in_session(self._dispatch_frequent_reminders)

    async def _run_in_session(
        self,
        handler: Callable[[UserRepository, TaskRepository, ClientRepository, ReminderService], Awaitable[None]],
    ) -> None:
        async with async_session_factory() as session:
            user_repository = UserRepository(session)
            task_repository = TaskRepository(session)
            client_repository = ClientRepository(session)
            reminder_service = ReminderService(task_repository=task_repository, client_repository=client_repository)
            await handler(user_repository, task_repository, client_repository, reminder_service)

    async def _dispatch_daily_summary(
        self,
        user_repository: UserRepository,
        task_repository: TaskRepository,
        client_repository: ClientRepository,
        reminder_service: ReminderService,
    ) -> None:
        await self._sender.send_daily_summaries(user_repository=user_repository, reminder_service=reminder_service)

    async def _dispatch_frequent_reminders(
        self,
        user_repository: UserRepository,
        task_repository: TaskRepository,
        client_repository: ClientRepository,
        reminder_service: ReminderService,
    ) -> None:
        await self._sender.send_task_and_contact_reminders(
            user_repository=user_repository,
            reminder_service=reminder_service,
            horizon_minutes=self._upcoming_task_horizon_minutes,
        )