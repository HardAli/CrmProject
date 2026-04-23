from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from app.common.http.http_client import HttpClient
from app.schemas.parsed_property import RawParsedPropertyData
from app.services.parsers.base import BaseParser
from app.services.parsers.krisha_extractors import extract_by_regex_map, extract_structured_payloads, find_text_fallback

logger = logging.getLogger(__name__)


class KrishaParser(BaseParser):
    source = "krisha"

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.endswith("krisha.kz")

    async def parse(self, url: str) -> RawParsedPropertyData:
        html = await self._http_client.get_text(url)
        listing_id_match = re.search(r"/a/show/(\d+)", url)
        listing_id = listing_id_match.group(1) if listing_id_match else None

        payloads = extract_structured_payloads(html)
        regex_data = extract_by_regex_map(html)

        merged: dict[str, object] = {"structured": payloads, "regex": regex_data}
        warnings: list[str] = []

        if not payloads:
            warnings.append("Structured data blocks not found; used HTML/text fallbacks")

        if "description" not in regex_data:
            text_fallback = find_text_fallback(html, "Описание")
            if text_fallback:
                merged["text_description_hint"] = text_fallback
                warnings.append("Description extracted from text fallback")

        logger.info("Krisha parser result source_url=%s listing_id=%s payload_keys=%s", url, listing_id, list(merged.keys()))
        return RawParsedPropertyData(
            source=self.source,
            source_url=url,
            source_listing_id=listing_id,
            payload=merged,
            html_text=html,
            parse_warnings=warnings,
        )