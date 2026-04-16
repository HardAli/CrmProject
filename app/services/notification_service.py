from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.common.formatters.notification_formatter import (
    format_contact_reminder,
    format_daily_summary,
    format_task_reminder,
)
from app.database.models.client import Client
from app.database.models.task import Task
from app.database.models.user import User
from app.services.reminder_service import DailySummary

logger = logging.getLogger(__name__)


class NotificationService:
    """Simple sender with in-memory anti-spam guard.

    NOTE: This guard is process-local. For horizontally scaled production
    deployments use Redis/shared storage with TTL.
    """

    def __init__(
        self,
        *,
        summary_cooldown_hours: int = 20,
        reminder_cooldown_minutes: int = 60,
    ) -> None:
        self._summary_sent_at: dict[tuple[int, date], datetime] = {}
        self._entity_sent_at: dict[str, datetime] = {}
        self._summary_cooldown = timedelta(hours=summary_cooldown_hours)
        self._reminder_cooldown = timedelta(minutes=reminder_cooldown_minutes)

    async def send_daily_summary(self, bot: Bot, user: User, summary: DailySummary) -> bool:
        if not summary.has_data or not user.telegram_id:
            return False

        today = datetime.now(tz=timezone.utc).date()
        guard_key = (user.id, today)
        now_dt = datetime.now(tz=timezone.utc)

        previous = self._summary_sent_at.get(guard_key)
        if previous and now_dt - previous < self._summary_cooldown:
            return False

        text = format_daily_summary(
            today_tasks_count=summary.today_tasks_count,
            overdue_tasks_count=summary.overdue_tasks_count,
            today_contacts_count=summary.today_contacts_count,
            overdue_contacts_count=summary.overdue_contacts_count,
            today_tasks=summary.today_tasks,
            overdue_tasks=summary.overdue_tasks,
            today_contacts=summary.today_contacts,
        )
        if not await self._safe_send(bot=bot, telegram_id=user.telegram_id, text=text):
            return False

        self._summary_sent_at[guard_key] = now_dt
        return True

    async def send_task_reminder(self, bot: Bot, user: User, task: Task) -> bool:
        return await self._send_entity(
            bot=bot,
            user=user,
            guard_key=f"task:{user.id}:{task.id}:{task.status.value}",
            text=format_task_reminder(task),
        )

    async def send_contact_reminder(self, bot: Bot, user: User, client: Client) -> bool:
        return await self._send_entity(
            bot=bot,
            user=user,
            guard_key=f"contact:{user.id}:{client.id}",
            text=format_contact_reminder(client),
        )

    async def _send_entity(self, *, bot: Bot, user: User, guard_key: str, text: str) -> bool:
        if not user.telegram_id:
            return False

        now_dt = datetime.now(tz=timezone.utc)
        previous = self._entity_sent_at.get(guard_key)
        if previous and now_dt - previous < self._reminder_cooldown:
            return False

        if not await self._safe_send(bot=bot, telegram_id=user.telegram_id, text=text):
            return False

        self._entity_sent_at[guard_key] = now_dt
        return True

    @staticmethod
    async def _safe_send(*, bot: Bot, telegram_id: int, text: str) -> bool:
        try:
            await bot.send_message(chat_id=telegram_id, text=text)
            return True
        except TelegramForbiddenError:
            logger.warning("Cannot send notification: user blocked bot", extra={"telegram_id": telegram_id})
            return False
        except TelegramBadRequest:
            logger.exception("Cannot send notification due to bad request", extra={"telegram_id": telegram_id})
            return False