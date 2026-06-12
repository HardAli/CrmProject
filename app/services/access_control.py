from __future__ import annotations

from app.common.enums import UserRole
from app.database.models.user import User


FULL_ACCESS_ROLES = {UserRole.ADMIN, UserRole.SUPERVISOR}


def role_has_full_access(role: UserRole | str | None) -> bool:
    if role is None:
        return False
    try:
        return UserRole(role) in FULL_ACCESS_ROLES
    except ValueError:
        return False


def has_full_access(user: User | None) -> bool:
    return bool(user and role_has_full_access(user.role))


def is_admin_or_supervisor(user: User | None) -> bool:
    return has_full_access(user)


def can_view_all_data(user: User | None) -> bool:
    return has_full_access(user)


def can_manage_users(user: User | None) -> bool:
    return has_full_access(user)


def can_export_database(user: User | None) -> bool:
    return has_full_access(user)
