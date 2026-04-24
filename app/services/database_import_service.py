from __future__ import annotations

import io
import json
import logging
import zipfile
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.client import Client
from app.database.models.client_log import ClientLog
from app.database.models.client_photo import ClientPhoto
from app.database.models.client_property import ClientProperty
from app.database.models.property import Property
from app.database.models.role_pass import RolePass
from app.database.models.showing import Showing
from app.database.models.task import Task
from app.database.models.user import User
from app.services.import_mappers import map_import_record_to_model_fields

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EntityImportStats:
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0


@dataclass(slots=True)
class DatabaseImportReport:
    export_version: int | str
    schema_version: str
    entity_stats: dict[str, EntityImportStats]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class InvalidDatabaseArchiveError(ValueError):
    pass


class DatabaseImportService:
    IMPORT_ORDER = [
        "users",
        "clients",
        "properties",
        "tasks",
        "client_logs",
        "client_properties",
        "showings",
        "client_photos",
        "role_passes",
    ]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def import_archive(self, payload: bytes) -> DatabaseImportReport:
        metadata, entities = self._read_archive(payload)
        report = DatabaseImportReport(
            export_version=metadata.get("export_version", "unknown"),
            schema_version=str(metadata.get("schema_version", "unknown")),
            entity_stats={name: EntityImportStats() for name in self.IMPORT_ORDER},
        )
        id_map: dict[str, dict[int, int]] = {name: {} for name in self.IMPORT_ORDER}

        await self._import_users(entities.get("users", []), report, id_map)
        await self._import_clients(entities.get("clients", []), report, id_map)
        await self._import_properties(entities.get("properties", []), report, id_map)
        await self._import_tasks(entities.get("tasks", []), report, id_map)
        await self._import_client_logs(entities.get("client_logs", []), report, id_map)
        await self._import_client_properties(entities.get("client_properties", []), report, id_map)
        await self._import_showings(entities.get("showings", []), report, id_map)
        await self._import_client_photos(entities.get("client_photos", []), report, id_map)
        await self._import_role_passes(entities.get("role_passes", []), report, id_map)

        return report

    def _read_archive(self, payload: bytes) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
        try:
            with zipfile.ZipFile(io.BytesIO(payload), mode="r") as zf:
                if "metadata.json" not in zf.namelist():
                    raise InvalidDatabaseArchiveError("Файл metadata.json отсутствует в архиве")

                metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
                entities: dict[str, list[dict[str, Any]]] = {}
                for entity_name in metadata.get("entities", []):
                    file_name = f"data/{entity_name}.json"
                    if file_name not in zf.namelist():
                        entities[entity_name] = []
                        continue
                    entities[entity_name] = json.loads(zf.read(file_name).decode("utf-8"))
        except zipfile.BadZipFile as exc:
            raise InvalidDatabaseArchiveError("Файл не является zip-архивом экспорта") from exc
        except json.JSONDecodeError as exc:
            raise InvalidDatabaseArchiveError("Архив содержит некорректный JSON") from exc

        if not isinstance(metadata, dict):
            raise InvalidDatabaseArchiveError("Некорректный metadata.json")
        if "export_version" not in metadata or "schema_version" not in metadata:
            raise InvalidDatabaseArchiveError("В metadata отсутствуют export_version/schema_version")

        return metadata, entities

    async def _import_users(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        await self._import_with_natural_key(
            entity_name="users",
            records=records,
            model=User,
            report=report,
            id_map=id_map,
            finder=self._find_user,
        )

    async def _import_clients(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        await self._import_with_natural_key(
            entity_name="clients",
            records=records,
            model=Client,
            report=report,
            id_map=id_map,
            finder=self._find_client,
            relation_mapper=lambda data: self._replace_ids(data, manager_id=id_map["users"]),
        )

    async def _import_properties(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        await self._import_with_natural_key(
            entity_name="properties",
            records=records,
            model=Property,
            report=report,
            id_map=id_map,
            finder=self._find_property,
            relation_mapper=lambda data: self._replace_ids(data, manager_id=id_map["users"]),
        )

    async def _import_tasks(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        await self._import_simple_create(
            entity_name="tasks",
            model=Task,
            records=records,
            report=report,
            id_map=id_map,
            relation_mapper=lambda data: self._replace_ids(data, client_id=id_map["clients"], assigned_to=id_map["users"]),
        )

    async def _import_client_logs(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        await self._import_simple_create(
            entity_name="client_logs",
            model=ClientLog,
            records=records,
            report=report,
            id_map=id_map,
            relation_mapper=lambda data: self._replace_ids(data, client_id=id_map["clients"], user_id=id_map["users"]),
        )

    async def _import_client_properties(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        stats = report.entity_stats["client_properties"]
        for record in records:
            stats.processed += 1
            old_id = record.get("id")
            mapped = map_import_record_to_model_fields(record, ClientProperty)
            data = self._replace_ids(mapped.data, client_id=id_map["clients"], property_id=id_map["properties"])
            data.pop("id", None)
            if self._has_mapping_gap(data, mapped.data, "client_id", "property_id"):
                stats.skipped += 1
                report.warnings.append("client_properties: отсутствует mapping по client_id/property_id")
                continue

            existing = await self._session.scalar(
                select(ClientProperty).where(
                    ClientProperty.client_id == data["client_id"],
                    ClientProperty.property_id == data["property_id"],
                )
            )
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                stats.updated += 1
                if isinstance(old_id, int):
                    id_map["client_properties"][old_id] = existing.id
                continue

            entity = ClientProperty(**data)
            self._session.add(entity)
            await self._session.flush()
            stats.created += 1
            if isinstance(old_id, int):
                id_map["client_properties"][old_id] = entity.id

    async def _import_showings(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        await self._import_simple_create(
            entity_name="showings",
            model=Showing,
            records=records,
            report=report,
            id_map=id_map,
            relation_mapper=lambda data: self._replace_ids(
                data,
                client_id=id_map["clients"],
                property_id=id_map["properties"],
                manager_id=id_map["users"],
            ),
        )

    async def _import_client_photos(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        stats = report.entity_stats["client_photos"]
        for record in records:
            stats.processed += 1
            old_id = record.get("id")
            mapped = map_import_record_to_model_fields(record, ClientPhoto)
            data = self._replace_ids(mapped.data, client_id=id_map["clients"], uploaded_by=id_map["users"])
            data.pop("id", None)
            if self._has_mapping_gap(data, mapped.data, "client_id", "uploaded_by"):
                stats.skipped += 1
                report.warnings.append("client_photos: отсутствует mapping по client_id/uploaded_by")
                continue

            existing = await self._session.scalar(
                select(ClientPhoto).where(
                    ClientPhoto.client_id == data["client_id"],
                    ClientPhoto.telegram_file_id == data.get("telegram_file_id"),
                )
            )
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                stats.updated += 1
                if isinstance(old_id, int):
                    id_map["client_photos"][old_id] = existing.id
                continue

            entity = ClientPhoto(**data)
            self._session.add(entity)
            await self._session.flush()
            stats.created += 1
            if isinstance(old_id, int):
                id_map["client_photos"][old_id] = entity.id

    async def _import_role_passes(self, records: list[dict[str, Any]], report: DatabaseImportReport, id_map: dict[str, dict[int, int]]) -> None:
        await self._import_with_natural_key(
            entity_name="role_passes",
            records=records,
            model=RolePass,
            report=report,
            id_map=id_map,
            finder=self._find_role_pass,
            relation_mapper=lambda data: self._replace_ids(
                data,
                created_by=id_map["users"],
                used_by=id_map["users"],
            ),
        )

    async def _import_with_natural_key(
        self,
        *,
        entity_name: str,
        records: list[dict[str, Any]],
        model: type[Any],
        report: DatabaseImportReport,
        id_map: dict[str, dict[int, int]],
        finder: Any,
        relation_mapper: Any | None = None,
    ) -> None:
        stats = report.entity_stats[entity_name]
        for record in records:
            stats.processed += 1
            old_id = record.get("id")
            try:
                mapped = map_import_record_to_model_fields(record, model)
                if mapped.conversion_errors:
                    stats.skipped += 1
                    report.warnings.append(f"{entity_name}: ошибки конвертации: {', '.join(mapped.conversion_errors)}")
                    continue

                data = dict(mapped.data)
                if relation_mapper is not None:
                    data = relation_mapper(data)

                data.pop("id", None)
                required_missing = [field for field in mapped.missing_required_fields if field not in data]
                if required_missing:
                    stats.skipped += 1
                    report.warnings.append(f"{entity_name}: пропуск записи из-за обязательных полей {required_missing}")
                    continue

                existing = await finder(data)
                if existing is None:
                    entity = model(**data)
                    self._session.add(entity)
                    await self._session.flush()
                    stats.created += 1
                    if isinstance(old_id, int):
                        id_map[entity_name][old_id] = entity.id
                    continue

                for key, value in data.items():
                    setattr(existing, key, value)
                await self._session.flush()
                stats.updated += 1
                if isinstance(old_id, int):
                    id_map[entity_name][old_id] = existing.id
            except Exception as exc:
                logger.exception("Import error entity=%s old_id=%s", entity_name, old_id)
                stats.errors += 1
                report.errors.append(f"{entity_name}: id={old_id} -> {exc}")

    async def _import_simple_create(
        self,
        *,
        entity_name: str,
        model: type[Any],
        records: list[dict[str, Any]],
        report: DatabaseImportReport,
        id_map: dict[str, dict[int, int]],
        relation_mapper: Any | None = None,
    ) -> None:
        stats = report.entity_stats[entity_name]
        for record in records:
            stats.processed += 1
            old_id = record.get("id")
            try:
                mapped = map_import_record_to_model_fields(record, model)
                if mapped.conversion_errors:
                    stats.skipped += 1
                    report.warnings.append(f"{entity_name}: ошибки конвертации: {', '.join(mapped.conversion_errors)}")
                    continue

                data = dict(mapped.data)
                if relation_mapper is not None:
                    data = relation_mapper(data)
                data.pop("id", None)

                required_missing = [field for field in mapped.missing_required_fields if field not in data]
                if required_missing:
                    stats.skipped += 1
                    report.warnings.append(f"{entity_name}: пропуск записи из-за обязательных полей {required_missing}")
                    continue

                if self._has_mapping_gap(data, mapped.data, *[k for k in ("client_id", "assigned_to", "user_id", "property_id", "manager_id") if k in mapped.data]):
                    stats.skipped += 1
                    report.warnings.append(f"{entity_name}: отсутствует mapping для внешних ключей")
                    continue

                entity = model(**data)
                self._session.add(entity)
                await self._session.flush()
                stats.created += 1
                if isinstance(old_id, int):
                    id_map[entity_name][old_id] = entity.id
            except Exception as exc:
                logger.exception("Import error entity=%s old_id=%s", entity_name, old_id)
                stats.errors += 1
                report.errors.append(f"{entity_name}: id={old_id} -> {exc}")

    async def _find_user(self, data: dict[str, Any]) -> User | None:
        telegram_id = data.get("telegram_id")
        if telegram_id is None:
            return None
        return await self._session.scalar(select(User).where(User.telegram_id == telegram_id))

    async def _find_client(self, data: dict[str, Any]) -> Client | None:
        phone = data.get("phone")
        if phone is None:
            return None
        return await self._session.scalar(select(Client).where(Client.phone == phone))

    async def _find_property(self, data: dict[str, Any]) -> Property | None:
        link = data.get("link")
        if link:
            found_by_link = await self._session.scalar(select(Property).where(Property.link == link))
            if found_by_link is not None:
                return found_by_link

        title = data.get("title")
        owner_phone = data.get("owner_phone")
        address = data.get("address")
        if title and owner_phone and address:
            return await self._session.scalar(
                select(Property).where(
                    Property.title == title,
                    Property.owner_phone == owner_phone,
                    Property.address == address,
                )
            )
        return None

    async def _find_role_pass(self, data: dict[str, Any]) -> RolePass | None:
        code = data.get("code")
        if code is None:
            return None
        return await self._session.scalar(select(RolePass).where(RolePass.code == code))

    @staticmethod
    def _replace_ids(data: dict[str, Any], **mappings: dict[int, int]) -> dict[str, Any]:
        result = dict(data)
        for field, mapping in mappings.items():
            old_value = result.get(field)
            if old_value is None:
                continue
            if isinstance(old_value, int) and old_value in mapping:
                result[field] = mapping[old_value]
        return result

    @staticmethod
    def _has_mapping_gap(mapped_data: dict[str, Any], original_data: dict[str, Any], *fields: str) -> bool:
        for field in fields:
            if field not in original_data:
                continue
            old_value = original_data.get(field)
            new_value = mapped_data.get(field)
            if isinstance(old_value, int) and isinstance(new_value, int) and old_value == new_value:
                return True
        return False