from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

_PHONE_PATTERN = re.compile(r"^\+?[0-9\-()\s]{10,20}$")


def normalize_phone(raw_phone: str) -> str:
    value = raw_phone.strip()
    if not value:
        raise ValueError("Телефон не должен быть пустым.")
    if not _PHONE_PATTERN.fullmatch(value):
        raise ValueError("Телефон должен содержать 10-20 символов: цифры, +, пробел, -, ().")

    normalized = re.sub(r"[^0-9+]", "", value)
    if normalized.startswith("8") and len(normalized) == 11:
        normalized = "+7" + normalized[1:]
    elif not normalized.startswith("+"):
        normalized = "+" + normalized

    if not re.fullmatch(r"\+[0-9]{10,15}", normalized):
        raise ValueError("Телефон после нормализации должен быть в формате +79991234567.")
    return normalized


def parse_money(raw_value: str) -> Decimal:
    normalized = raw_value.strip().replace(" ", "").replace(",", ".")
    if not normalized:
        raise ValueError("Значение не должно быть пустым.")
    try:
        value = Decimal(normalized)
    except InvalidOperation as error:
        raise ValueError("Введите корректное число для бюджета.") from error

    if value < 0:
        raise ValueError("Бюджет не может быть отрицательным.")
    return value


def parse_next_contact_at(raw_value: str) -> datetime:
    value = raw_value.strip()
    if not value:
        raise ValueError("Дата не должна быть пустой.")

    formats = (
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
    )
    for dt_format in formats:
        try:
            parsed = datetime.strptime(value, dt_format)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue

    raise ValueError("Неверный формат даты. Пример: 25.04.2026 14:30")