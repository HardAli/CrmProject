from __future__ import annotations

import logging

from app.common.utils.phone_links import normalize_owner_phone
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.client_properties import ClientPropertyRepository
from app.repositories.clients import ClientRepository

logger = logging.getLogger(__name__)


class AutoLinkService:
    def __init__(self, client_repository: ClientRepository, client_property_repository: ClientPropertyRepository) -> None:
        self._client_repository = client_repository
        self._client_property_repository = client_property_repository

    async def auto_link_property_by_phone(self, *, current_user: User, property_obj: Property) -> int:
        try:
            normalized_phone = normalize_owner_phone(property_obj.owner_phone)
        except ValueError:
            return 0

        candidates = {normalized_phone, normalized_phone.replace("+", "8", 1)}
        clients = await self._client_repository.get_by_phone_candidates(list(candidates), manager_id=current_user.id)
        linked_count = 0
        for client in clients:
            existing = await self._client_property_repository.get_existing(client_id=client.id, property_id=property_obj.id)
            if existing is not None:
                continue
            await self._client_property_repository.create(client_id=client.id, property_id=property_obj.id)
            linked_count += 1

        logger.info("Auto-link finished property_id=%s linked_clients_count=%s", property_obj.id, linked_count)
        return linked_count