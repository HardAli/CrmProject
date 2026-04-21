from __future__ import annotations

from app.common.utils.parsers import normalize_phone


def normalize_owner_phone(raw_phone: str) -> str:
    return normalize_phone(raw_phone)


def format_owner_phone(phone: str) -> str:
    return format_phone_for_copy(phone)


def format_phone_for_copy(phone: str) -> str:
    normalized = normalize_owner_phone(phone)
    return f"<code>{normalized}</code>"


def build_whatsapp_url(phone: str) -> str:
    normalized = normalize_owner_phone(phone)
    return f"https://wa.me/{normalized[1:]}"