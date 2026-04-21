from __future__ import annotations

from collections.abc import Sequence

from app.common.enums import UserRole
from app.database.models.client import Client
from app.database.models.client_photo import ClientPhoto
from app.database.models.user import User
from app.repositories.client_photo_repository import ClientPhotoRepository
from app.repositories.clients import ClientRepository


class ClientPhotoService:
    def __init__(self, client_photo_repository: ClientPhotoRepository, client_repository: ClientRepository) -> None:
        self._client_photo_repository = client_photo_repository
        self._client_repository = client_repository

    async def add_client_photo(
        self,
        current_user: User,
        client_id: int,
        telegram_file_id: str,
        caption: str | None = None,
    ) -> ClientPhoto:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")

        if not self.can_manage_client_photos(current_user=current_user, client=client):
            raise PermissionError("Недостаточно прав для добавления фото")

        clean_caption = caption.strip() if caption else None
        if clean_caption == "":
            clean_caption = None

        return await self._client_photo_repository.create(
            client_id=client.id,
            telegram_file_id=telegram_file_id,
            uploaded_by=current_user.id,
            caption=clean_caption,
        )

    async def get_client_photos(self, current_user: User, client_id: int, limit: int = 20) -> Sequence[ClientPhoto]:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")

        return await self._client_photo_repository.get_by_client(client_id=client.id, limit=limit)

    async def delete_client_photo(self, current_user: User, photo_id: int) -> bool:
        photo = await self._client_photo_repository.get_by_id(photo_id)
        if photo is None:
            raise ValueError("Фото не найдено")

        if not self.can_manage_client_photos(current_user=current_user, client=photo.client):
            raise PermissionError("Недостаточно прав для удаления фото")

        return await self._client_photo_repository.delete(photo_id=photo_id)

    async def get_client_photo(self, current_user: User, photo_id: int) -> ClientPhoto:
        photo = await self._client_photo_repository.get_by_id(photo_id)
        if photo is None:
            raise ValueError("Фото не найдено")

        if not self.can_view_client_photos(current_user=current_user, client=photo.client):
            raise PermissionError("Недостаточно прав для просмотра фото")

        return photo

    async def count_client_photos(self, current_user: User, client_id: int) -> int:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")
        return await self._client_photo_repository.count_by_client(client.id)

    async def can_manage_client_photos_for_client(self, current_user: User, client_id: int) -> bool:
        client = await self._get_client_with_view_check(current_user=current_user, client_id=client_id)
        if client is None:
            raise ValueError("Клиент не найден или недоступен")
        return self.can_manage_client_photos(current_user=current_user, client=client)

    def can_manage_client_photos(self, current_user: User, client: Client) -> bool:
        if current_user.role == UserRole.ADMIN:
            return True

        if current_user.role == UserRole.MANAGER:
            return client.manager_id == current_user.id

        return False

    def can_view_client_photos(self, current_user: User, client: Client) -> bool:
        if current_user.role in {UserRole.ADMIN, UserRole.SUPERVISOR}:
            return True

        if current_user.role == UserRole.MANAGER:
            return client.manager_id == current_user.id

        return False

    async def _get_client_with_view_check(self, current_user: User, client_id: int) -> Client | None:
        client = await self._client_repository.get_by_id(client_id)
        if client is None:
            return None

        if not self.can_view_client_photos(current_user=current_user, client=client):
            return None

        return client