from __future__ import annotations

from app.common.formatters.property_address_formatter import format_property_address_for_display
from app.common.utils.formatters import format_area
from app.common.utils.telegram_text import truncate_text
from app.schemas.parsed_property import ParsedPropertyData

MAX_PREVIEW_LENGTH = 3500
MAX_LINE_VALUE_LENGTH = 180
MAX_DESCRIPTION_LENGTH = 500
MAX_WARNING_LENGTH = 140
MAX_WARNINGS_COUNT = 5
MAX_IMAGE_URLS_PREVIEW = 3


def format_property_import_preview(parsed_data: ParsedPropertyData) -> str:
    def line_value(value: object, *, limit: int = MAX_LINE_VALUE_LENGTH) -> str:
        return truncate_text(str(value) if value not in (None, "") else "—", limit)

    warnings = [truncate_text(item, MAX_WARNING_LENGTH) for item in parsed_data.parse_warnings[:MAX_WARNINGS_COUNT]]
    warnings_extra = max(0, len(parsed_data.parse_warnings) - MAX_WARNINGS_COUNT)
    warning_lines = [f"• {item}" for item in warnings] or ["—"]
    if warnings_extra:
        warning_lines.append(f"• Ещё предупреждений: {warnings_extra}")

    missing_lines = [f"• {field}" for field in parsed_data.missing_required_fields] or ["—"]

    photo_count = len(parsed_data.image_urls)
    photo_preview_items = parsed_data.image_urls[:MAX_IMAGE_URLS_PREVIEW]
    photo_preview = ", ".join(truncate_text(url, 80) for url in photo_preview_items) if photo_preview_items else "—"
    if photo_count > MAX_IMAGE_URLS_PREVIEW:
        photo_preview = f"{photo_preview} (+{photo_count - MAX_IMAGE_URLS_PREVIEW})"

    rows = [
        "🏠 Предпросмотр импорта",
        "",
        f"Название: {line_value(parsed_data.title)}",
        f"Тип: {line_value(parsed_data.property_type.value if parsed_data.property_type else None)}",
        f"Район: {line_value(parsed_data.district)}",
        f"Адрес: {line_value(format_property_address_for_display(parsed_data.district, parsed_data.address))}",
        f"Цена: {line_value(parsed_data.price)}",
        f"Площадь: {line_value(format_area(parsed_data.area))}",
        f"Комнаты: {line_value(parsed_data.rooms)}",
        f"Этаж: {line_value(parsed_data.floor)}",
        f"Этажность: {line_value(parsed_data.building_floors)}",
        f"Телефон: {line_value(parsed_data.owner_phone)}",
        f"Ссылка: {line_value(parsed_data.source_url)}",
        f"Описание: {truncate_text(parsed_data.description or '—', MAX_DESCRIPTION_LENGTH)}",
        f"Фото: {photo_count}",
        f"URL фото (кратко): {photo_preview}",
        "",
        "Missing fields:",
        *missing_lines,
        "",
        "Warnings:",
        *warning_lines,
    ]
    return truncate_text("\n".join(rows), MAX_PREVIEW_LENGTH)
