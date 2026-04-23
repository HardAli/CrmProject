from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.parsed_property import RawParsedPropertyData


class BaseParser(ABC):
    source: str

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def parse(self, url: str) -> RawParsedPropertyData:
        raise NotImplementedError