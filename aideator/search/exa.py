"""Exa search provider implementation.

Uses the Exa API for AI-native search.
Requires EXA_API_KEY environment variable.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from aideator.search.providers import Document, ProviderStatus, SearchProvider, SearchResult

LOGGER = logging.getLogger(__name__)

EXA_API_URL = "https://api.exa.ai"


class ExaSearchProvider(SearchProvider):
    """Search provider using the Exa API.

    Exa provides AI-native search with semantic understanding.
    Requires an API key (paid, with free trial credits).

    Capabilities:
    - web_search: Semantic web search
    - url_extract: Content extraction from URLs
    """

    DEFAULT_TIMEOUT = 30.0

    def __init__(self, api_key: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                },
            )
        return self._client

    @property
    def name(self) -> str:
        return "exa"

    @property
    def requires_api_key(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        mode: str = "general",
    ) -> list[SearchResult]:
        """Search using Exa API.

        Args:
            query: Search query
            limit: Max results
            mode: 'general' or 'research'

        Returns:
            List of SearchResult
        """
        if not self._api_key:
            return []

        client = await self._get_client()

        payload: dict[str, Any] = {
            "query": query,
            "num_results": min(limit, 20),
            "use_autoprompt": True,
            "type": "auto",
        }

        # Include text content for richer snippets
        payload["contents"] = {"text": {"max_characters": 500}}

        try:
            response = await client.post(f"{EXA_API_URL}/search", json=payload)
            if response.status_code == 429:
                LOGGER.warning("Exa rate limit hit", extra={"event": "exa_rate_limit"})
                return []
                
            response.raise_for_status()
            data = response.json()

            results: list[SearchResult] = []
            for item in data.get("results", []):
                snippet = str(item.get("text", item.get("highlight", "")))
                results.append(
                    SearchResult(
                        title=str(item.get("title", "")),
                        url=str(item.get("url", "")),
                        snippet=snippet,
                        source="exa",
                        score=float(item.get("score", 0.0)),
                    )
                )
            return results

        except (httpx.HTTPStatusError, httpx.TimeoutException):
            raise
        except Exception:
            return []

    async def fetch(self, url: str) -> Document:
        """Fetch content using Exa contents endpoint.

        Args:
            url: URL to extract content from

        Returns:
            Document with extracted text
        """
        if not self._api_key:
            return Document(url=url, text="API key not configured")

        client = await self._get_client()

        try:
            payload = {
                "ids": [url],
                "contents": {"text": True},
            }
            response = await client.post(f"{EXA_API_URL}/contents", json=payload)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if results:
                first = results[0]
                return Document(
                    url=url,
                    title=str(first.get("title", "")),
                    text=str(first.get("text", "")),
                )
            return Document(url=url, text="No content extracted")

        except Exception as e:
            return Document(url=url, text=f"Error: {e}")

    async def healthcheck(self) -> ProviderStatus:
        """Check if Exa API is accessible."""
        if not self._api_key:
            return ProviderStatus.NOT_CONFIGURED

        try:
            client = await self._get_client()
            payload = {
                "query": "test",
                "num_results": 1,
            }
            response = await client.post(
                f"{EXA_API_URL}/search", json=payload, timeout=10.0
            )
            if response.status_code == 200:
                return ProviderStatus.OK
            if response.status_code == 429:
                return ProviderStatus.RATELIMIT
            if response.status_code in (401, 403):
                return ProviderStatus.NOT_CONFIGURED
            return ProviderStatus.ERROR
        except httpx.TimeoutException:
            return ProviderStatus.TIMEOUT
        except httpx.ConnectError:
            return ProviderStatus.UNAVAILABLE
        except Exception:
            return ProviderStatus.ERROR

    def capabilities(self) -> set[str]:
        """Exa supports search and content extraction."""
        return {"web_search", "url_extract"}

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
