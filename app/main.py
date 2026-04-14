from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.middlewares.db_session import DbSessionMiddleware
from app.bot.routers import setup_routers
from app.config.settings import get_settings
from app.database.session import async_session_factory, engine


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def run_polling() -> None:
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()

    dispatcher.update.outer_middleware(DbSessionMiddleware(async_session_factory))
    setup_routers(dispatcher)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


def main() -> None:
    configure_logging()
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()