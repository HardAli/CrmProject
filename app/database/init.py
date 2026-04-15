from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.base import Base
from app.database.session import engine

# IMPORTANT: importing models registers all tables in Base.metadata.
from app.database import models as _models  # noqa: F401

logger = logging.getLogger(__name__)


async def init_database() -> None:
    """Initialize database connection and ensure schema objects exist."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
    except SQLAlchemyError:
        logger.exception("Failed to connect to database")
        raise

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("Database schema is initialized")
    except SQLAlchemyError:
        logger.exception("Failed to initialize database schema")
        raise