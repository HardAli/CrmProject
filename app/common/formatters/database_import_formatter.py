from __future__ import annotations

from html import escape

from app.services.database_import_service import DatabaseImportReport


def format_database_import_report(report: DatabaseImportReport) -> str:
    lines = [
        "<b>Импорт завершён</b>",
        "",
        f"<b>Экспорт:</b> v{escape(str(report.export_version))}",
        f"<b>Схема экспорта:</b> {escape(str(report.schema_version))}",
        "",
        "<b>Статистика:</b>",
    ]

    for entity, stats in report.entity_stats.items():
        lines.append(
            f"• {escape(entity)}: обработано {stats.processed}, создано {stats.created}, "
            f"обновлено {stats.updated}, пропущено {stats.skipped}, ошибок {stats.errors}"
        )

    lines.extend(
        [
            "",
            f"<b>Warnings:</b> {len(report.warnings)}",
            f"<b>Errors:</b> {len(report.errors)}",
        ]
    )

    if report.warnings:
        lines.append("\n<b>Последние warnings:</b>")
        lines.extend(f"• {escape(item)}" for item in report.warnings[-5:])

    if report.errors:
        lines.append("\n<b>Последние errors:</b>")
        lines.extend(f"• {escape(item)}" for item in report.errors[-5:])

    return "\n".join(lines)