from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserRole
from app.database.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(self) -> list[User]:
        stmt = (
            select(User)
            .where(User.is_active.is_(True), User.telegram_id.is_not(None))
            .order_by(User.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, telegram_id: int, full_name: str, role: UserRole) -> User:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            role=role,
            is_active=True,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def set_role(self, user: User, role: UserRole) -> None:
        user.role = role
        await self._session.flush()
