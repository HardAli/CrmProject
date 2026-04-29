from __future__ import annotations

from aiogram.types import Message

from app.common.utils.telegram_text import split_message

DEFAULT_SAFE_MESSAGE_LIMIT = 3500


async def safe_answer(
    message: Message,
    text: str,
    *,
    max_length: int = DEFAULT_SAFE_MESSAGE_LIMIT,
    reply_markup=None,
    parse_mode: str | None = None,
) -> None:
    chunks = split_message(text, max_length=max_length)
    for index, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            reply_markup=reply_markup if index == len(chunks) - 1 else None,
            parse_mode=parse_mode,
        )
