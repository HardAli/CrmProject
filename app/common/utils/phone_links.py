from __future__ import annotations

from app.common.utils.parsers import normalize_phone


def normalize_owner_phone(raw_phone: str) -> str:
    return normalize_phone(raw_phone)


def build_tel_url_or_none(phone: str | None) -> str | None:
    if not phone:
        return None

    try:
        normalized = normalize_owner_phone(phone)
    except ValueError:
        return None

    return f"tel:{normalized}"


def format_owner_phone(phone: str) -> str:
    normalized = normalize_owner_phone(phone)
    digits = normalized[1:]

    if len(digits) == 11 and digits.startswith("7"):
        return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

    return normalized


def build_tel_url(phone: str) -> str:
    tel_url = build_tel_url_or_none(phone)
    if tel_url is None:
        raise ValueError("Телефон не удалось преобразовать в tel-ссылку.")
    return tel_url


def build_whatsapp_url(phone: str) -> str:
    normalized = normalize_owner_phone(phone)
    return f"https://wa.me/{normalized[1:]}"