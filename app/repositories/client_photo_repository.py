from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models.client_photo import ClientPhoto


class ClientPhotoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        client_id: int,
        telegram_file_id: str,
        telegram_file_unique_id: str | None,
        uploaded_by: int,
        caption: str | None = None,
    ) -> ClientPhoto:
        client_photo = ClientPhoto(
            client_id=client_id,
            telegram_file_id=telegram_file_id,
            telegram_file_unique_id=telegram_file_unique_id,
            uploaded_by=uploaded_by,
            caption=caption,
        )
        self._session.add(client_photo)
        await self._session.flush()
        await self._session.refresh(client_photo)
        return client_photo

    async def get_by_client(self, client_id: int, limit: int | None = None) -> Sequence[ClientPhoto]:
        stmt = select(ClientPhoto).where(ClientPhoto.client_id == client_id).order_by(ClientPhoto.created_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, photo_id: int) -> ClientPhoto | None:
        stmt = (
            select(ClientPhoto)
            .options(joinedload(ClientPhoto.client), joinedload(ClientPhoto.uploaded_by_user))
            .where(ClientPhoto.id == photo_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, photo_id: int) -> bool:
        photo = await self.get_by_id(photo_id)
        if photo is None:
            return False
        await self._session.delete(photo)
        await self._session.flush()
        return True

    async def count_by_client(self, client_id: int) -> int:
        stmt = select(func.count(ClientPhoto.id)).where(ClientPhoto.client_id == client_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_for_client(
        self,
        *,
        client_id: int,
        telegram_file_id: str,
        telegram_file_unique_id: str | None,
    ) -> bool:
        if telegram_file_unique_id:
            duplicate_filter = ClientPhoto.telegram_file_unique_id == telegram_file_unique_id
        else:
            duplicate_filter = ClientPhoto.telegram_file_id == telegram_file_id

        stmt = (
            select(ClientPhoto.id)
            .where(and_(ClientPhoto.client_id == client_id, duplicate_filter))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
