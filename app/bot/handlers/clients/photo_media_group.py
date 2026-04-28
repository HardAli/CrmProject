from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

PhotoPayload = tuple[str, str | None]

_MEDIA_GROUP_BUFFER: dict[str, list[PhotoPayload]] = {}
_MEDIA_GROUP_TASKS: dict[str, asyncio.Task[None]] = {}
_MEDIA_GROUP_DELAY_SECONDS = 1.0


async def buffer_media_group_photo(
    *,
    key: str,
    photo: PhotoPayload,
    on_ready: Callable[[list[PhotoPayload]], Awaitable[None]],
    delay_seconds: float = _MEDIA_GROUP_DELAY_SECONDS,
) -> None:
    _MEDIA_GROUP_BUFFER.setdefault(key, []).append(photo)
    if key in _MEDIA_GROUP_TASKS:
        return

    async def _flush() -> None:
        try:
            await asyncio.sleep(delay_seconds)
            photos = _MEDIA_GROUP_BUFFER.pop(key, [])
            if photos:
                await on_ready(photos)
        finally:
            _MEDIA_GROUP_TASKS.pop(key, None)

    _MEDIA_GROUP_TASKS[key] = asyncio.create_task(_flush())
