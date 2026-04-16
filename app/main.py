from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.exc import SQLAlchemyError

from app.bot.middlewares.db_session import DbSessionMiddleware
from app.bot.routers import setup_routers
from app.config.settings import get_settings
from app.database.init import init_database
from app.database.session import async_session_factory, engine
from app.workers.scheduler import ReminderScheduler


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def run_polling() -> None:
    settings = get_settings()

    await init_database()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()

    dispatcher.update.outer_middleware(DbSessionMiddleware(async_session_factory))
    setup_routers(dispatcher)

    reminder_scheduler = ReminderScheduler(
        bot=bot,
        daily_summary_hour_utc=settings.reminder_daily_summary_hour_utc,
        frequent_check_minutes=settings.reminder_check_interval_minutes,
        upcoming_task_horizon_minutes=settings.reminder_task_horizon_minutes,
    )

    await bot.delete_webhook(drop_pending_updates=True)
    reminder_scheduler.start()
    try:
        await dispatcher.start_polling(bot)
    except SQLAlchemyError:
        logger.exception("Database error during bot polling")
        raise
    finally:
        await reminder_scheduler.shutdown()
        await bot.session.close()
        await engine.dispose()


def main() -> None:
    configure_logging()
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()