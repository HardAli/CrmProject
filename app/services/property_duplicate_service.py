from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.common.dto.properties import CreatePropertyDTO
from app.database.models.property import Property
from app.repositories.properties import PropertyRepository


MATCH_FIELDS = ("owner_phone_normalized", "floor", "building_floors", "building_year", "price", "rooms", "area")


@dataclass
class DuplicateCheckResult:
    duplicate_found: bool
    matched_fields_count: int
    matched_fields: list[str]
    matched_property: Property | None


class PropertyDuplicateService:
    def __init__(self, property_repository: PropertyRepository) -> None:
        self._property_repository = property_repository

    async def find_best_duplicate(self, candidate_data: CreatePropertyDTO) -> DuplicateCheckResult:
        candidates = await self._property_repository.list_for_duplicate_check(limit=300)
        best: tuple[int, list[str], Property | None] = (0, [], None)
        for existing in candidates:
            matched_fields = self.compare_property(candidate_data, existing)
            if len(matched_fields) > best[0]:
                best = (len(matched_fields), matched_fields, existing)

        return DuplicateCheckResult(
            duplicate_found=best[0] >= 5,
            matched_fields_count=best[0],
            matched_fields=best[1],
            matched_property=best[2],
        )

    def compare_property(self, candidate: CreatePropertyDTO, existing: Property) -> list[str]:
        matched: list[str] = []
        if self._norm_phone(candidate.owner_phone) and self._norm_phone(candidate.owner_phone) == self._norm_phone(existing.owner_phone):
            matched.append("owner_phone_normalized")
        if self._eq_int(candidate.floor, existing.floor):
            matched.append("floor")
        if self._eq_int(candidate.building_floors, existing.building_floors):
            matched.append("building_floors")
        if self._eq_int(candidate.building_year, existing.building_year):
            matched.append("building_year")
        if self._eq_decimal(candidate.price, existing.price):
            matched.append("price")
        if self._eq_int(candidate.rooms, existing.rooms):
            matched.append("rooms")
        if self._eq_decimal(candidate.area, existing.area):
            matched.append("area")
        return matched

    @staticmethod
    def _norm_phone(value: str | None) -> str | None:
        if not value:
            return None
        return ''.join(ch for ch in value if ch.isdigit())

    @staticmethod
    def _eq_int(a: object, b: object) -> bool:
        if a in (None, "") or b in (None, ""):
            return False
        try:
            return int(a) == int(b)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _eq_decimal(a: object, b: object) -> bool:
        if a in (None, "") or b in (None, ""):
            return False
        try:
            return Decimal(str(a)) == Decimal(str(b))
        except Exception:
            return False
