from __future__ import annotations

import logging

from app.database.models.property import Property
from app.repositories.property_photos import PropertyPhotoRepository

logger = logging.getLogger(__name__)


class PropertyPhotoService:
    def __init__(self, property_photo_repository: PropertyPhotoRepository) -> None:
        self._property_photo_repository = property_photo_repository

    async def attach_photo_urls(self, *, property_obj: Property, image_urls: list[str]) -> int:
        if not image_urls:
            return 0
        created_count = await self._property_photo_repository.add_urls(
            property_id=property_obj.id,
            urls=image_urls,
        )
        logger.info(
            "Property photo URLs saved property_id=%s incoming=%s created=%s",
            property_obj.id,
            len(image_urls),
            created_count,
        )
        return created_count
