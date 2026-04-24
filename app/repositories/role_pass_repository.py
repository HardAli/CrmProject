from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserRole
from app.database.models.role_pass import RolePass


class RolePassRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pass(self, *, code: str, target_role: UserRole, created_by: int, expires_at: datetime) -> RolePass:
        role_pass = RolePass(
            code=code,
            target_role=target_role,
            created_by=created_by,
            expires_at=expires_at,
            is_used=False,
        )
        self._session.add(role_pass)
        await self._session.flush()
        return role_pass

    async def get_by_code(self, code: str) -> RolePass | None:
        stmt = select(RolePass).where(RolePass.code == code).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_code(self, code: str) -> RolePass | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(RolePass)
            .where(
                RolePass.code == code,
                RolePass.is_used.is_(False),
                RolePass.expires_at > now,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_as_used(self, *, pass_id: int, used_by: int, used_at: datetime) -> None:
        stmt = select(RolePass).where(RolePass.id == pass_id).limit(1)
        result = await self._session.execute(stmt)
        role_pass = result.scalar_one_or_none()
        if role_pass is None:
            return
        role_pass.is_used = True
        role_pass.used_by = used_by
        role_pass.used_at = used_at
        await self._session.flush()

    async def get_recent_passes(self, *, created_by: int, limit: int = 10) -> list[RolePass]:
        stmt = (
            select(RolePass)
            .where(RolePass.created_by == created_by)
            .order_by(desc(RolePass.id))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())