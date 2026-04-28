from __future__ import annotations

import re

from app.common.utils.parsers import normalize_phone


def normalize_owner_phone(raw_phone: str) -> str:
    return normalize_phone(raw_phone)


def format_owner_phone(phone: str) -> str:
    return format_phone_for_copy(phone)


def format_phone_for_copy(phone: str) -> str:
    normalized = normalize_owner_phone(phone)
    return f"<code>{normalized}</code>"


def normalize_phone_for_whatsapp(phone: str | None) -> str | None:
    if phone is None:
        return None
    return normalize_phone_digits(phone)


def normalize_phone_digits(phone: str | None) -> str | None:
    if phone is None:
        return None
    digits = re.sub(r"\D", "", str(phone))
    if not digits:
        return None
    if len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"
    return digits


def format_phone_for_display(phone: str | None) -> str:
    digits = normalize_phone_digits(phone)
    if digits is None:
        return "—"
    return f"+{digits}"


def build_tel_url(phone: str | None) -> str | None:
    display_phone = format_phone_for_display(phone)
    if display_phone == "—":
        return None
    return f"tel:{display_phone}"


def format_phone_for_copy_plain(phone: str | None) -> str:
    return format_phone_for_display(phone)


def build_whatsapp_url(phone: str | None) -> str | None:
    normalized = normalize_phone_for_whatsapp(phone)
    if normalized is None:
        return None
    return f"https://wa.me/{normalized}"
