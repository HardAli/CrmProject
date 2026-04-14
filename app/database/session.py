from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from typing import Any
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings

settings = get_settings()

_VALID_SSLMODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
_SSLMODE_ALIASES = {
    "verify_ca": "verify-ca",
    "verify_full": "verify-full",
    "enabled": "require",
    "true": "require",
    "1": "require",
}


def _normalize_sslmode(sslmode: str) -> str:
    normalized_sslmode = _SSLMODE_ALIASES.get(sslmode.strip().lower(), sslmode.strip().lower())
    normalized_sslmode = normalized_sslmode.replace("_", "-")
    if normalized_sslmode not in _VALID_SSLMODES:
        valid_values = ", ".join(sorted(_VALID_SSLMODES))
        msg = f"Invalid sslmode '{sslmode}'. Expected one of: {valid_values}"
        raise ValueError(msg)

    return normalized_sslmode


def _build_async_database_config(raw_url: str) -> tuple[str, dict[str, Any]]:
    parsed_url = make_url(raw_url)
    connect_args: dict[str, Any] = {}

    if parsed_url.drivername == "postgresql":
        parsed_url = parsed_url.set(drivername="postgresql+asyncpg")

    sslmode = parsed_url.query.get("sslmode")
    if sslmode is not None:
        normalized_sslmode = _normalize_sslmode(sslmode)
        connect_args["ssl"] = normalized_sslmode != "disable"

        query_params = dict(parsed_url.query)
        query_params.pop("sslmode", None)
        parsed_url = parsed_url.set(query=query_params)

    return parsed_url.render_as_string(hide_password=False), connect_args


DATABASE_URL, DATABASE_CONNECT_ARGS = _build_async_database_config(settings.database_url)

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
    connect_args=DATABASE_CONNECT_ARGS,
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
