from __future__ import annotations

import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)


class HttpClientError(RuntimeError):
    """HTTP client transport or protocol failure."""


class HttpResponseError(HttpClientError):
    def __init__(self, *, status_code: int, url: str) -> None:
        super().__init__(f"HTTP {status_code} for {url}")
        self.status_code = status_code
        self.url = url


class HttpClient:
    def __init__(
        self,
        *,
        timeout_seconds: int = 15,
        retries: int = 2,
        user_agent: str = "CRMPropertyImporter/1.0 (+TelegramBot)",
    ) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._retries = retries
        self._user_agent = user_agent

    async def get_text(self, url: str) -> str:
        headers = {"User-Agent": self._user_agent, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"}
        for attempt in range(self._retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=self._timeout, headers=headers) as session:
                    async with session.get(url, allow_redirects=True) as response:
                        if response.status != 200:
                            raise HttpResponseError(status_code=response.status, url=url)
                        return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as error:
                logger.warning("HTTP fetch failed (attempt=%s, url=%s): %s", attempt + 1, url, error)
                if attempt >= self._retries:
                    raise HttpClientError(f"Failed to fetch {url}") from error
                await asyncio.sleep(0.5 * (attempt + 1))
        raise HttpClientError(f"Failed to fetch {url}")