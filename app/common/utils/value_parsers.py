from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def parse_decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    text = str(value).strip()
    if not text:
        return None

    text = text.replace(" ", "").replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)
    if not match:
        return None

    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None


def parse_int_or_none(value: object) -> int | None:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    text = str(value).strip()
    if not text:
        return None

    match = re.search(r"\d+", text)
    if not match:
        return None

    return int(match.group(0))
