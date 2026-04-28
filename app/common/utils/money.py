from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_CURRENCY_TOKENS = ("тенге", "тг", "kzt", "₸")
_MILLION_TOKENS = ("млн", "миллион", "миллиона", "миллионов")
_THOUSAND_TOKENS = ("тыс", "тысяч")


def parse_money_to_tenge(value: object) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    text = str(value).strip().lower()
    if not text:
        return None

    text = text.replace(",", ".")
    for token in _CURRENCY_TOKENS:
        text = text.replace(token, " ")

    compact_text = re.sub(r"\s+", " ", text).strip()
    has_million = any(token in compact_text for token in _MILLION_TOKENS)
    has_thousand = any(token in compact_text for token in _THOUSAND_TOKENS)
    has_k_suffix = bool(re.search(r"\d\s*[кk]\b", compact_text))

    normalized_number_text = compact_text.replace(" ", "")
    match = re.search(r"\d+(?:\.\d+)?", normalized_number_text)
    if not match:
        return None

    try:
        number = Decimal(match.group(0))
    except InvalidOperation:
        return None

    if number < 0:
        return None

    if has_million:
        return number * Decimal("1000000")

    if has_thousand or has_k_suffix:
        return number * Decimal("1000")

    if number < Decimal("10000"):
        return number * Decimal("1000000")

    return number


def parse_money_range_to_tenge(text: str | None) -> tuple[Decimal | None, Decimal | None]:
    if text is None:
        return None, None

    raw = str(text).strip().lower()
    if not raw:
        return None, None

    if raw.startswith("до "):
        return None, parse_money_to_tenge(raw.replace("до", "", 1).strip())

    if raw.startswith("от "):
        return parse_money_to_tenge(raw.replace("от", "", 1).strip()), None

    if raw.endswith("+"):
        return parse_money_to_tenge(raw[:-1].strip()), None

    if "-" in raw:
        left, right = raw.split("-", 1)
        return parse_money_to_tenge(left.strip()), parse_money_to_tenge(right.strip())

    return None, parse_money_to_tenge(raw)


def format_price_short(value: Decimal | int | float | None) -> str:
    if value is None:
        return "—"

    decimal_value = Decimal(str(value))

    if decimal_value >= Decimal("1000000"):
        millions = decimal_value / Decimal("1000000")
        text = f"{millions.normalize():f}".rstrip("0").rstrip(".")
        return f"{text} млн"

    if decimal_value >= Decimal("1000"):
        thousands = decimal_value / Decimal("1000")
        text = f"{thousands.normalize():f}".rstrip("0").rstrip(".")
        return f"{text} тыс"

    return f"{decimal_value:,.0f}".replace(",", " ")
