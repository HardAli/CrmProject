from __future__ import annotations

from app.database.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def check_access(self, telegram_id: int) -> bool:
        user = await self._user_repository.get_by_telegram_id(telegram_id)
        return bool(user and user.is_active)

    async def get_active_user_by_telegram_id(self, telegram_id: int) -> User | None:
        user = await self._user_repository.get_by_telegram_id(telegram_id)
        if user is None or not user.is_active:
            return None
        return user