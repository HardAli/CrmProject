from __future__ import annotations

import logging

from app.database.models.property import Property

logger = logging.getLogger(__name__)


class PropertyPhotoService:
    """MVP photo importer: keeps external URLs only and logs attach attempt."""

    async def attach_photo_urls(self, *, property_obj: Property, image_urls: list[str]) -> int:
        if not image_urls:
            return 0
        # MVP: no DB table for property photos yet.
        logger.info("Property photo URLs captured property_id=%s count=%s", property_obj.id, len(image_urls))
        return len(image_urls)