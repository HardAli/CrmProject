from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)


class ReminderSender:
    def __init__(self, bot: Bot, notification_service: NotificationService) -> None:
        self._bot = bot
        self._notification_service = notification_service

    async def send_daily_summaries(self, user_repository: UserRepository, reminder_service: ReminderService) -> None:
        users = await user_repository.get_active_users()
        for user in users:
            summary = await reminder_service.build_daily_summary_for_user(user)
            sent = await self._notification_service.send_daily_summary(self._bot, user, summary)
            if sent:
                logger.info("Daily summary sent", extra={"user_id": user.id})

    async def send_task_and_contact_reminders(
        self,
        user_repository: UserRepository,
        reminder_service: ReminderService,
        *,
        horizon_minutes: int,
    ) -> None:
        users = await user_repository.get_active_users()
        now_dt = datetime.now(tz=timezone.utc)

        for user in users:
            upcoming_tasks = await reminder_service.collect_upcoming_tasks(
                user=user,
                now_dt=now_dt,
                horizon_minutes=horizon_minutes,
            )
            for task in upcoming_tasks:
                await self._notification_service.send_task_reminder(self._bot, user, task)

            today_contacts = await reminder_service.collect_today_contacts(user=user, target_date=now_dt.date())
            for client in today_contacts:
                await self._notification_service.send_contact_reminder(self._bot, user, client)