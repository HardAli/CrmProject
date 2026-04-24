from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Sequence

from app.database.models.role_pass import RolePass
from app.database.models.user import User


def format_role_pass(role_pass: RolePass) -> str:
    expires_at = role_pass.expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    return (
        f"🔐 <b>Одноразовый пароль создан</b>\n\n"
        f"<b>Роль:</b> {escape(role_pass.target_role.value)}\n"
        f"<b>Код:</b> <code>{escape(role_pass.code)}</code>\n"
        f"<b>Действует до:</b> {expires_at}"
    )


def format_users_list(users: Sequence[User], *, limit: int) -> str:
    if not users:
        return "Пользователи не найдены."

    rows = ["<b>Пользователи:</b>", ""]
    for index, user in enumerate(users, start=1):
        name = user.full_name.strip() if user.full_name else "Неизвестно"
        rows.append(
            f"{index}. ID={user.id} | tg={user.telegram_id}\n"
            f"   👤 {escape(name)}\n"
            f"   🛡 {escape(user.role.value)} | active={user.is_active}"
        )

    rows.extend(["", f"Показаны первые {min(len(users), limit)} записей."])
    return "\n".join(rows)


def format_pass_error(reason: str | None) -> str:
    if reason == "used":
        return "Этот одноразовый пароль уже использован."
    if reason == "expired":
        return "Срок действия одноразового пароля истёк."
    return "Неверный одноразовый пароль."


def format_role_applied(role: str) -> str:
    return f"Роль <b>{escape(role)}</b> успешно выдана."