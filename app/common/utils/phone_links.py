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
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return None
    return digits


def build_whatsapp_url(phone: str | None) -> str | None:
    normalized = normalize_phone_for_whatsapp(phone)
    if normalized is None:
        return None
    return f"https://wa.me/{normalized}"