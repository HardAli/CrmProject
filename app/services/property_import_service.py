from __future__ import annotations

import logging
import re
from dataclasses import asdict
from decimal import Decimal
from urllib.parse import urlparse

from app.common.dto.properties import CreatePropertyDTO
from app.common.enums import PropertyStatus
from app.common.utils.formatters import format_area
from app.common.utils.money import parse_money_to_tenge
from app.common.utils.property_fields import normalize_building_material, parse_building_year_or_none
from app.common.utils.value_parsers import parse_decimal_or_none, parse_int_or_none
from app.database.models.property import Property
from app.database.models.user import User
from app.services.auto_link_service import AutoLinkService
from app.services.parsers.base import BaseParser
from app.services.parsers.normalizers import normalize_parsed_data
from app.services.properties import PropertyService
from app.services.property_photo_service import PropertyPhotoService
from app.schemas.parsed_property import ParsedPropertyData, RawParsedPropertyData

logger = logging.getLogger(__name__)


class InvalidListingUrlError(ValueError):
    pass


class UnsupportedSourceError(ValueError):
    pass


class ParseFailedError(RuntimeError):
    pass


class PropertyImportService:
    REQUIRED_FIELDS = ("title", "property_type", "district", "address", "owner_phone", "price", "area", "rooms", "floor", "status")

    def __init__(
        self,
        *,
        property_service: PropertyService,
        photo_service: PropertyPhotoService,
        auto_link_service: AutoLinkService,
        parsers: list[BaseParser],
    ) -> None:
        self._property_service = property_service
        self._photo_service = photo_service
        self._auto_link_service = auto_link_service
        self._parsers = parsers

    def validate_url(self, url: str) -> str:
        value = (url or "").strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidListingUrlError("Некорректная ссылка. Нужен полный URL с http/https.")
        if "krisha.kz" not in parsed.netloc:
            raise InvalidListingUrlError("Сейчас поддерживаются только ссылки krisha.kz")
        if not re.search(r"/a/show/\d+", parsed.path):
            raise InvalidListingUrlError("Ссылка должна вести на карточку объявления вида /a/show/<id>")
        return value

    def detect_source(self, url: str) -> str:
        for parser in self._parsers:
            if parser.can_handle(url):
                return parser.source
        raise UnsupportedSourceError("Источник ссылки пока не поддерживается.")

    async def parse_listing(self, url: str) -> RawParsedPropertyData:
        for parser in self._parsers:
            if parser.can_handle(url):
                logger.info("Start parsing listing source=%s url=%s", parser.source, url)
                return await parser.parse(url)
        raise UnsupportedSourceError("Источник ссылки пока не поддерживается.")

    def normalize_parsed_data(self, raw_data: RawParsedPropertyData) -> ParsedPropertyData:
        parsed = normalize_parsed_data(raw_data)
        parsed.missing_required_fields = self.collect_missing_fields(parsed)
        return parsed

    def collect_missing_fields(self, parsed_data: ParsedPropertyData) -> list[str]:
        missing = [field for field in self.REQUIRED_FIELDS if getattr(parsed_data, field, None) in (None, "")]
        if parsed_data.property_type and parsed_data.property_type.value == "apartment" and parsed_data.building_floors is None:
            missing.append("building_floors")
        return missing

    def build_preview(self, parsed_data: ParsedPropertyData) -> str:
        photo_count = len(parsed_data.image_urls)
        warning_lines = "\n".join(f"• {item}" for item in parsed_data.parse_warnings) or "—"
        missing_lines = "\n".join(f"• {item}" for item in parsed_data.missing_required_fields) or "—"
        return (
            "🏠 Предпросмотр импорта\n\n"
            f"Название: {parsed_data.title or '—'}\n"
            f"Тип: {parsed_data.property_type.value if parsed_data.property_type else '—'}\n"
            f"Район: {parsed_data.district or '—'}\n"
            f"Адрес: {parsed_data.address or '—'}\n"
            f"Цена: {parsed_data.price or '—'}\n"
            f"Площадь: {format_area(parsed_data.area)}\n"
            f"Кухня: {format_area(parsed_data.kitchen_area)}\n"
            f"Комнаты: {parsed_data.rooms or '—'}\n"
            f"Этаж: {parsed_data.floor if parsed_data.floor is not None else '—'}\n"
            f"Этажность: {parsed_data.building_floors if parsed_data.building_floors is not None else '—'}\n"
            f"Год постройки: {parsed_data.building_year if parsed_data.building_year is not None else '—'}\n"
            f"Материал дома: {parsed_data.building_material or '—'}\n"
            f"Телефон: {parsed_data.owner_phone or '—'}\n"
            f"Описание: {(parsed_data.description or '—')[:300]}\n"
            f"Ссылка: {parsed_data.source_url}\n"
            f"Фото: {photo_count}\n\n"
            f"Missing fields:\n{missing_lines}\n\n"
            f"Warnings:\n{warning_lines}"
        )

    async def create_property_from_parsed_data(self, *, current_user: User, parsed_data: ParsedPropertyData) -> tuple[Property, int, int]:
        dto = CreatePropertyDTO(
            title=parsed_data.title or "Без названия",
            property_type=parsed_data.property_type,
            district=parsed_data.district or "Не указан",
            address=parsed_data.address or "Не указан",
            owner_phone=parsed_data.owner_phone or "+70000000000",
            price=parse_money_to_tenge(parsed_data.price) or Decimal(0),
            area=parse_decimal_or_none(parsed_data.area) or Decimal(0),
            kitchen_area=parse_decimal_or_none(parsed_data.kitchen_area),
            rooms=parse_int_or_none(parsed_data.rooms),
            floor=parse_int_or_none(parsed_data.floor),
            building_floors=parse_int_or_none(parsed_data.building_floors),
            building_year=parse_building_year_or_none(parsed_data.building_year),
            building_material=normalize_building_material(parsed_data.building_material),
            description=parsed_data.description,
            link=parsed_data.source_url,
            status=parsed_data.status or PropertyStatus.ACTIVE,
            manager_id=current_user.id,
        )
        logger.debug(
            "Creating property from parsed data: rooms=%r floor=%r building_floors=%r area=%r price=%r",
            dto.rooms,
            dto.floor,
            dto.building_floors,
            dto.area,
            dto.price,
        )
        property_obj, _ = await self._property_service.create_property(current_user=current_user, data=dto)

        photo_count = await self.import_photos_if_possible(property_obj=property_obj, parsed_data=parsed_data)
        linked_clients_count = await self.run_auto_link_if_possible(current_user=current_user, property_obj=property_obj, parsed_data=parsed_data)

        logger.info(
            "Property import completed property_id=%s linked_clients_count=%s photo_count=%s missing_fields=%s",
            property_obj.id,
            linked_clients_count,
            photo_count,
            parsed_data.missing_required_fields,
        )
        return property_obj, linked_clients_count, photo_count

    async def import_photos_if_possible(self, *, property_obj: Property, parsed_data: ParsedPropertyData) -> int:
        try:
            return await self._photo_service.attach_photo_urls(property_obj=property_obj, image_urls=parsed_data.image_urls)
        except Exception:
            logger.exception("Photo import failed for property_id=%s", property_obj.id)
            return 0

    async def run_auto_link_if_possible(self, *, current_user: User, property_obj: Property, parsed_data: ParsedPropertyData) -> int:
        if not parsed_data.owner_phone:
            return 0
        try:
            return await self._auto_link_service.auto_link_property_by_phone(current_user=current_user, property_obj=property_obj)
        except Exception:
            logger.exception("Auto-link failed for property_id=%s", property_obj.id)
            return 0

    @staticmethod
    def to_state_payload(parsed_data: ParsedPropertyData) -> dict[str, object]:
        payload = asdict(parsed_data)
        payload["property_type"] = parsed_data.property_type.value if parsed_data.property_type else None
        payload["status"] = parsed_data.status.value if parsed_data.status else PropertyStatus.ACTIVE.value
        payload["price"] = str(parsed_data.price) if parsed_data.price is not None else None
        payload["area"] = str(parsed_data.area) if parsed_data.area is not None else None
        payload["kitchen_area"] = str(parsed_data.kitchen_area) if parsed_data.kitchen_area is not None else None
        return payload
