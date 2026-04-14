from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings

settings = get_settings()


def _build_async_database_url(raw_url: str) -> str:
    parsed_url = make_url(raw_url)

    if parsed_url.drivername == "postgresql":
        parsed_url = parsed_url.set(drivername="postgresql+asyncpg")

    return parsed_url.render_as_string(hide_password=False)


DATABASE_URL = _build_async_database_url(settings.database_url)

if DATABASE_URL.startswith("postgresql+asyncpg://"):
    try:
        import asyncpg  # noqa: F401
    except ModuleNotFoundError as exc:  # pragma: no cover - startup guard
        msg = (
            "Database URL uses the asyncpg driver, but dependency 'asyncpg' is missing. "
            "Install it with: pip install asyncpg"
        )
        raise RuntimeError(msg) from exc


engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
