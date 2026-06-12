from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.buyer_offer_history import BuyerOfferHistory
from app.database.models.buyer_request import BuyerRequest
from app.database.models.client import Client
from app.database.models.client_log import ClientLog
from app.database.models.client_photo import ClientPhoto
from app.database.models.client_property import ClientProperty
from app.database.models.property import Property
from app.database.models.property_photo import PropertyPhoto
from app.database.models.property_selection import PropertySelection
from app.database.models.property_selection_feedback import PropertySelectionFeedback
from app.database.models.property_selection_item import PropertySelectionItem
from app.database.models.role_pass import RolePass
from app.database.models.showing import Showing
from app.database.models.task import Task
from app.database.models.user import User
from app.services.export_serializers import serialize_model_instance


@dataclass(slots=True)
class DatabaseExportResult:
    file_name: str
    payload: bytes
    metadata: dict[str, Any]
    counters: dict[str, int]


class DatabaseExportService:
    EXPORT_VERSION = 1
    EXPORT_FORMAT = "crm.entities.zip"
    SCHEMA_VERSION = "20260611_0017_independent_property_selections"

    ENTITY_MODELS: list[tuple[str, type[Any]]] = [
        ("users", User),
        ("clients", Client),
        ("buyer_requests", BuyerRequest),
        ("properties", Property),
        ("property_photos", PropertyPhoto),
        ("property_selections", PropertySelection),
        ("property_selection_items", PropertySelectionItem),
        ("property_selection_feedback", PropertySelectionFeedback),
        ("buyer_offer_history", BuyerOfferHistory),
        ("tasks", Task),
        ("client_logs", ClientLog),
        ("client_properties", ClientProperty),
        ("showings", Showing),
        ("client_photos", ClientPhoto),
        ("role_passes", RolePass),
    ]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def export(self) -> DatabaseExportResult:
        entities_payload: dict[str, list[dict[str, Any]]] = {}
        counters: dict[str, int] = {}

        for entity_name, model in self.ENTITY_MODELS:
            rows = (await self._session.execute(select(model))).scalars().all()
            serialized = [serialize_model_instance(row) for row in rows]
            entities_payload[entity_name] = serialized
            counters[entity_name] = len(serialized)

        metadata = {
            "format": self.EXPORT_FORMAT,
            "export_version": self.EXPORT_VERSION,
            "schema_version": self.SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entities": list(entities_payload.keys()),
            "entity_counters": counters,
        }

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
            for entity_name, records in entities_payload.items():
                zf.writestr(f"data/{entity_name}.json", json.dumps(records, ensure_ascii=False, indent=2))

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return DatabaseExportResult(
            file_name=f"crm_export_{timestamp}.zip",
            payload=archive.getvalue(),
            metadata=metadata,
            counters=counters,
        )
