from __future__ import annotations

from html import escape

from app.services.database_import_service import DatabaseImportReport


def format_database_import_report(report: DatabaseImportReport) -> str:
    lines = [
        "Импорт завершён",
        "",
        f"Экспорт: v{escape(str(report.export_version))}",
        f"Схема экспорта: {escape(str(report.schema_version))}",
        "",
        "Статистика:",
    ]

    for entity, stats in report.entity_stats.items():
        lines.append(
            f"• {escape(entity)}: обработано {stats.processed}, создано {stats.created}, "
            f"обновлено {stats.updated}, пропущено {stats.skipped}, ошибок {stats.errors}"
        )

    lines.extend(
        [
            "",
            f"Warnings: {len(report.warnings)}",
            f"Errors: {len(report.errors)}",
        ]
    )

    if report.warnings:
        lines.append("\nПоследние warnings:")
        lines.extend(f"• {escape(item)}" for item in report.warnings[-5:])

    if report.errors:
        lines.append("\nПоследние errors:")
        lines.extend(f"• {escape(item)}" for item in report.errors[-5:])

    return "\n".join(lines)