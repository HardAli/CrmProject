from __future__ import annotations


def format_import_success(*, property_id: int, linked_clients_count: int, photo_count: int) -> str:
    return (
        "✅ Объект успешно импортирован.\n"
        f"ID объекта: #{property_id}\n"
        f"Автопривязано клиентов: {linked_clients_count}\n"
        f"Обработано фото: {photo_count}"
    )