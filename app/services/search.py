from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.common.enums import ClientStatus, PropertyStatus, PropertyType, RequestType, UserRole
from app.common.utils.value_parsers import parse_int_or_none
from app.database.models.client import Client
from app.database.models.property import Property
from app.database.models.user import User
from app.repositories.clients import ClientRepository
from app.repositories.properties import PropertyRepository


class SearchService:
    MAX_LIMIT = 30
    DEFAULT_LIMIT = 10

    def __init__(self, client_repository: ClientRepository, property_repository: PropertyRepository) -> None:
        self._client_repository = client_repository
        self._property_repository = property_repository

    async def search_clients(self, current_user: User, filters: dict[str, Any]) -> list[Client]:
        validated = self.validate_client_search_filters(filters)
        manager_id = current_user.id if current_user.role == UserRole.MANAGER else None

        return list(
            await self._client_repository.search_clients(
                full_name=validated.get("full_name"),
                phone=validated.get("phone"),
                district=validated.get("district"),
                status=validated.get("status"),
                request_type=validated.get("request_type"),
                manager_id=manager_id,
                limit=validated["limit"],
            )
        )

    async def search_properties(self, current_user: User, filters: dict[str, Any]) -> list[Property]:
        validated = self.validate_property_search_filters(filters)
        manager_id = current_user.id if current_user.role == UserRole.MANAGER else None

        return list(
            await self._property_repository.search_properties(
                search_text=validated.get("search_text"),
                title=validated.get("title"),
                district=validated.get("district"),
                property_type=validated.get("property_type"),
                status=validated.get("status"),
                price_min=validated.get("price_min"),
                price_max=validated.get("price_max"),
                rooms=validated.get("rooms"),
                manager_id=manager_id,
                limit=validated["limit"],
            )
        )

    def validate_client_search_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        full_name = self._clean_text(filters.get("full_name"))
        phone = self._clean_text(filters.get("phone"))
        district = self._clean_text(filters.get("district"))

        status = self._enum_or_none(filters.get("status"), ClientStatus)
        request_type = self._enum_or_none(filters.get("request_type"), RequestType)

        validated = {
            "full_name": full_name,
            "phone": phone,
            "district": district,
            "status": status,
            "request_type": request_type,
            "limit": self._normalize_limit(filters.get("limit")),
        }
        self._ensure_at_least_one_filter(validated, keys=("full_name", "phone", "district", "status", "request_type"))
        return validated

    def validate_property_search_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        search_text = self._clean_text(filters.get("search_text"))
        title = self._clean_text(filters.get("title"))
        district = self._clean_text(filters.get("district"))
        property_type = self._enum_or_none(filters.get("property_type"), PropertyType)
        status = self._enum_or_none(filters.get("status"), PropertyStatus)
        price_min = self._decimal_or_none(filters.get("price_min"), field_name="price_min")
        price_max = self._decimal_or_none(filters.get("price_max"), field_name="price_max")
        rooms = self._rooms_or_none(filters.get("rooms"))

        if price_min is not None and price_max is not None and price_min > price_max:
            raise ValueError("Минимальная цена не может быть больше максимальной.")

        validated = {
            "search_text": search_text,
            "title": title,
            "district": district,
            "property_type": property_type,
            "status": status,
            "price_min": price_min,
            "price_max": price_max,
            "rooms": rooms,
            "limit": self._normalize_limit(filters.get("limit")),
        }
        self._ensure_at_least_one_filter(
            validated,
            keys=("search_text", "title", "district", "property_type", "status", "price_min", "price_max", "rooms"),
        )
        return validated

    @staticmethod
    def _ensure_at_least_one_filter(validated: dict[str, Any], keys: tuple[str, ...]) -> None:
        has_filter = any(validated.get(key) is not None for key in keys)
        if not has_filter:
            raise ValueError("Укажите минимум один параметр для поиска.")

    @classmethod
    def _normalize_limit(cls, value: Any) -> int:
        if value is None:
            return cls.DEFAULT_LIMIT

        try:
            parsed = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Некорректный лимит поиска.") from error

        if parsed <= 0:
            raise ValueError("Лимит должен быть больше 0.")
        return min(parsed, cls.MAX_LIMIT)

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _enum_or_none(value: Any, enum_cls: type) -> Any:
        if value is None:
            return None
        if isinstance(value, enum_cls):
            return value
        return enum_cls(str(value))

    @staticmethod
    def _decimal_or_none(value: Any, *, field_name: str) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            parsed = Decimal(str(value).replace(" ", "").replace(",", "."))
        except Exception as error:
            raise ValueError(f"Поле {field_name}: некорректное число.") from error

        if parsed < 0:
            raise ValueError(f"Поле {field_name}: число не может быть отрицательным.")
        return parsed

    @staticmethod
    def _rooms_or_none(value: Any) -> int | None:
        if value is None or value == "":
            return None
        if str(value).strip().lower() == "студия":
            return None
        parsed = parse_int_or_none(value)
        if parsed is not None and parsed > 0:
            return parsed
        raise ValueError("Поле rooms: укажите положительное число или «Студия».")
