"""Tavily search provider implementation.

Uses the Tavily API for AI-powered web search.
Requires TAVILY_API_KEY environment variable.
"""

from __future__ import annotations

from typing import Any

import httpx

from aideator.search.providers import Document, ProviderStatus, SearchProvider, SearchResult

TAVILY_API_URL = "https://api.tavily.com"


class TavilySearchProvider(SearchProvider):
    """Search provider using the Tavily API.

    Tavily provides AI-powered web search optimized for LLM applications.
    Requires an API key (free tier available with limited credits).

    Capabilities:
    - web_search: Full web search
    - url_extract: URL content extraction via Tavily extract endpoint
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
                headers={"Content-Type": "application/json"},
            )
        return self._client

    @property
    def name(self) -> str:
        return "tavily"

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
        """Search using Tavily API.

        Args:
            query: Search query
            limit: Max results (Tavily max is 20)
            mode: 'general' or 'research' (maps to search_depth)

        Returns:
            List of SearchResult
        """
        if not self._api_key:
            return []

        client = await self._get_client()

        payload: dict[str, Any] = {
            "api_key": self._api_key,
            "query": query,
            "max_results": min(limit, 20),
            "search_depth": "advanced" if mode == "research" else "basic",
            "include_answer": False,
        }

        try:
            response = await client.post(f"{TAVILY_API_URL}/search", json=payload)
            response.raise_for_status()
            data = response.json()

            results: list[SearchResult] = []
            for item in data.get("results", []):
                results.append(
                    SearchResult(
                        title=str(item.get("title", "")),
                        url=str(item.get("url", "")),
                        snippet=str(item.get("content", "")),
                        source="tavily",
                        score=float(item.get("score", 0.0)),
                    )
                )
            return results

        except (httpx.HTTPStatusError, httpx.TimeoutException):
            raise
        except Exception:
            return []

    async def fetch(self, url: str) -> Document:
        """Fetch content using Tavily extract endpoint.

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
                "api_key": self._api_key,
                "urls": [url],
            }
            response = await client.post(f"{TAVILY_API_URL}/extract", json=payload)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if results:
                first = results[0]
                return Document(
                    url=url,
                    title=str(first.get("title", "")),
                    text=str(first.get("raw_content", first.get("content", ""))),
                )
            return Document(url=url, text="No content extracted")

        except Exception as e:
            return Document(url=url, text=f"Error: {e}")

    async def healthcheck(self) -> ProviderStatus:
        """Check if Tavily API is accessible."""
        if not self._api_key:
            return ProviderStatus.NOT_CONFIGURED

        try:
            client = await self._get_client()
            # Light search to verify API key
            payload = {
                "api_key": self._api_key,
                "query": "test",
                "max_results": 1,
                "search_depth": "basic",
            }
            response = await client.post(
                f"{TAVILY_API_URL}/search", json=payload, timeout=10.0
            )
            if response.status_code == 200:
                return ProviderStatus.OK
            if response.status_code == 401:
                return ProviderStatus.NOT_CONFIGURED
            return ProviderStatus.ERROR
        except httpx.TimeoutException:
            return ProviderStatus.TIMEOUT
        except httpx.ConnectError:
            return ProviderStatus.UNAVAILABLE
        except Exception:
            return ProviderStatus.ERROR

    def capabilities(self) -> set[str]:
        """Tavily supports search and extraction."""
        return {"web_search", "url_extract"}

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
