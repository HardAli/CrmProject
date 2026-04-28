from __future__ import annotations

from decimal import Decimal, InvalidOperation


def format_decimal_plain(value: object, max_fraction_digits: int = 2) -> str:
    if value is None:
        return "—"

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)

    quantizer = Decimal(f"1.{'0' * max_fraction_digits}") if max_fraction_digits > 0 else Decimal("1")
    quantized = decimal_value.quantize(quantizer)
    text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def format_area(value: object) -> str:
    text = format_decimal_plain(value, max_fraction_digits=2)
    if text == "—":
        return text
    return f"{text} м²"


def format_area_compact(value: object) -> str:
    text = format_decimal_plain(value, max_fraction_digits=2)
    if text == "—":
        return text
    return f"{text}м²"
