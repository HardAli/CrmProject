from __future__ import annotations

from datetime import datetime
from html import escape

from app.services.database_export_service import DatabaseExportResult


def format_database_export_summary(result: DatabaseExportResult) -> str:
    created_at = datetime.fromisoformat(result.metadata["created_at"]).strftime("%d.%m.%Y %H:%M UTC")
    lines = [
        "<b>Экспорт базы готов</b>",
        "",
        f"<b>Формат:</b> {escape(str(result.metadata['format']))}",
        f"<b>Версия экспорта:</b> {escape(str(result.metadata['export_version']))}",
        f"<b>Версия схемы:</b> {escape(str(result.metadata['schema_version']))}",
        f"<b>Создан:</b> {escape(created_at)}",
        "",
        "<b>Сущности:</b>",
    ]
    for entity, count in result.counters.items():
        lines.append(f"• {escape(entity)}: {count}")
    return "\n".join(lines)