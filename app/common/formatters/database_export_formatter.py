from __future__ import annotations

from datetime import datetime
from html import escape

from app.services.database_export_service import DatabaseExportResult


def format_database_export_summary(result: DatabaseExportResult) -> str:
    created_at = datetime.fromisoformat(result.metadata["created_at"]).strftime("%d.%m.%Y %H:%M UTC")
    lines = [
        "Экспорт базы готов",
        "",
        f"Формат: {escape(str(result.metadata['format']))}",
        f"Версия экспорта: {escape(str(result.metadata['export_version']))}",
        f"Версия схемы: {escape(str(result.metadata['schema_version']))}",
        f"Создан: {escape(created_at)}",
        "",
        "Сущности:",
    ]
    for entity, count in result.counters.items():
        lines.append(f"• {escape(entity)}: {count}")
    return "\n".join(lines)