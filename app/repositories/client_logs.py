from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.enums import ClientActionType
from app.database.models.client_log import ClientLog


class ClientLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_log(
        self,
        client_id: int,
        user_id: int | None,
        action_type: ClientActionType,
        comment: str | None = None,
    ) -> ClientLog:
        log = ClientLog(
            client_id=client_id,
            user_id=user_id,
            action_type=action_type,
            comment=comment,
        )
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log

    async def get_recent_by_client(self, client_id: int, limit: int = 10) -> Sequence[ClientLog]:
        stmt = (
            select(ClientLog)
            .options(joinedload(ClientLog.user))
            .where(ClientLog.client_id == client_id)
            .order_by(ClientLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()