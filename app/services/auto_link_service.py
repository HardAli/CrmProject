from __future__ import annotations

import logging

from app.common.utils.phone_links import normalize_owner_phone
from app.common.enums import ClientActionType, ClientPropertyRelationStatus
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.client_logs import ClientLogRepository
from app.repositories.client_properties import ClientPropertyRepository
from app.repositories.clients import ClientRepository

logger = logging.getLogger(__name__)


class AutoLinkService:
    def __init__(
        self,
        client_repository: ClientRepository,
        client_property_repository: ClientPropertyRepository,
        client_log_repository: ClientLogRepository,
    ) -> None:
        self._client_repository = client_repository
        self._client_property_repository = client_property_repository
        self._client_log_repository = client_log_repository

    async def auto_link_property_by_phone(self, *, current_user: User, property_obj: Property) -> int:
        normalized_phone = (property_obj.owner_phone_normalized or "").strip()
        if not normalized_phone:
            try:
                normalized_phone = normalize_owner_phone(property_obj.owner_phone)
            except ValueError:
                return 0

        clients = list(await self._client_repository.get_all_by_phone_normalized(normalized_phone))
        linked_client_ids = await self._client_property_repository.get_linked_client_ids_for_property(
            property_id=property_obj.id,
            client_ids={client.id for client in clients},
        )
        linked_count = 0
        for client in clients:
            if client.id in linked_client_ids:
                continue
            await self._client_property_repository.create(
                client_id=client.id,
                property_id=property_obj.id,
                relation_status=ClientPropertyRelationStatus.SENT,
            )
            await self._client_log_repository.create_log(
                client_id=client.id,
                user_id=current_user.id,
                action_type=ClientActionType.AUTO_LINKED_BY_PHONE,
                comment=f"Связь с объектом #{property_obj.id} создана автоматически по номеру owner_phone",
            )
            linked_count += 1

        logger.info("Auto-link finished property_id=%s linked_clients_count=%s", property_obj.id, linked_count)
        return linked_count
