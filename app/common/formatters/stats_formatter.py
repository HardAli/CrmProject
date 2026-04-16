from __future__ import annotations

from collections.abc import Sequence

from app.common.dto.statistics import ManagerStatsRowDTO, StatsBundleDTO, StatsPeriod

PERIOD_LABELS: dict[StatsPeriod, str] = {
    StatsPeriod.TODAY: "сегодня",
    StatsPeriod.DAYS_30: "30 дней",
    StatsPeriod.ALL_TIME: "всё время",
}


def format_stats_bundle(*, title: str, period: StatsPeriod, stats: StatsBundleDTO) -> str:
    period_label = PERIOD_LABELS[period]
    client = stats.clients
    task = stats.tasks
    property_stats = stats.properties

    return (
        f"📊 <b>{title}</b>\n"
        f"Период: <b>{period_label}</b>\n\n"
        f"<b>Клиенты</b>\n"
        f"• Всего клиентов: {client.total}\n"
        f"• Новых клиентов: {client.new}\n"
        f"• В работе: {client.in_progress}\n"
        f"• Ждут звонка: {client.waiting}\n"
        f"• Показ: {client.showing}\n"
        f"• Закрыто: {client.closed_success}\n"
        f"• Отказов: {client.closed_failed}\n"
        f"• Контактов на сегодня: {client.contacts_today}\n"
        f"• Просроченных контактов: {client.contacts_overdue}\n\n"
        f"<b>Задачи</b>\n"
        f"• Открытых задач: {task.open_total}\n"
        f"• Задач на сегодня: {task.due_today}\n"
        f"• Просроченных задач: {task.overdue}\n"
        f"• Выполненных задач: {task.done}\n"
        f"• Задач в работе: {task.in_progress}\n\n"
        f"<b>Объекты</b>\n"
        f"• Всего объектов: {property_stats.total}\n"
        f"• Активных объектов: {property_stats.active}\n"
        f"• Проданных: {property_stats.sold}\n"
        f"• Сданных: {property_stats.reserved}\n"
        f"• Архивных: {property_stats.archived}"
    )


def format_lead_sources(*, period: StatsPeriod, stats: dict[str, int]) -> str:
    period_label = PERIOD_LABELS[period]
    if not stats:
        return f"📥 <b>Источники лидов</b>\nПериод: <b>{period_label}</b>\n\nДанных пока нет."

    rows = [f"📥 <b>Источники лидов</b>", f"Период: <b>{period_label}</b>", ""]
    for source, count in stats.items():
        rows.append(f"• {source} — {count}")
    return "\n".join(rows)


def format_manager_stats(*, period: StatsPeriod, rows: Sequence[ManagerStatsRowDTO]) -> str:
    period_label = PERIOD_LABELS[period]
    if not rows:
        return f"👥 <b>Статистика по менеджерам</b>\nПериод: <b>{period_label}</b>\n\nМенеджеры не найдены."

    lines: list[str] = [f"👥 <b>Статистика по менеджерам</b>", f"Период: <b>{period_label}</b>", ""]
    for row in rows:
        lines.extend(
            [
                f"<b>{row.manager_name}</b>",
                f"• клиентов: {row.clients_total}",
                f"• новых за период: {row.clients_new_period}",
                f"• задач на сегодня: {row.tasks_due_today}",
                f"• просрочено задач: {row.tasks_overdue}",
                f"• активных объектов: {row.properties_active}",
                "",
            ]
        )
    return "\n".join(lines).strip()