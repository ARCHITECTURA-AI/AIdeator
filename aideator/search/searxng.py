"""SearXNG search provider — self-hosted metasearch engine.

Requires a running SearXNG instance with JSON API enabled.
Zero external cost — runs on your own infrastructure.

SearXNG setup:
  docker run -d -p 8888:8080 searxng/searxng:latest
  # Enable JSON in settings.yml:
  #   search:
  #     formats: [html, json]
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

# Re-use the builtin HTML helpers for fetch()
from aideator.search.builtin import _extract_title, _html_to_text
from aideator.search.providers import Document, ProviderStatus, SearchProvider, SearchResult

LOGGER = logging.getLogger("aideator.search.searxng")

DEFAULT_INSTANCE_URL = "http://localhost:8888"


class SearXNGSearchProvider(SearchProvider):
    """Self-hosted SearXNG metasearch engine provider.

    SearXNG aggregates results from multiple search engines
    (Google, Bing, DuckDuckGo, etc.) without sharing your
    queries with any third party beyond your own server.

    Capabilities:
    - web_search: Full metasearch across configured engines
    - url_extract: URL content extraction (reuses builtin logic)
    """

    DEFAULT_TIMEOUT = 20.0
    MAX_CONTENT_LENGTH = 1_000_000  # 1 MB

    def __init__(
        self,
        instance_url: str = DEFAULT_INSTANCE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        # Normalise: strip trailing slash
        self._instance_url = instance_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; AIdeator/1.0; "
                        "+https://github.com/ARCHITECTURA-AI/AIdeator)"
                    ),
                    "Accept": "application/json, text/html",
                },
            )
        return self._client

    # ------------------------------------------------------------------ #
    # SearchProvider interface
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        return "searxng"

    @property
    def requires_api_key(self) -> bool:
        return False

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        mode: str = "general",
    ) -> list[SearchResult]:
        """Search via the SearXNG JSON API.

        Args:
            query: Search query string
            limit: Maximum results (SearXNG returns ~10 per page)
            mode: 'general' or 'research' (maps to categories)

        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            return []

        client = await self._get_client()

        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "pageno": 1,
        }

        # Map mode to SearXNG categories
        if mode == "research":
            params["categories"] = "science,it"

        try:
            response = await client.get(
                f"{self._instance_url}/search", params=params
            )
            response.raise_for_status()
            data = response.json()

            results: list[SearchResult] = []
            for item in data.get("results", [])[:limit]:
                results.append(
                    SearchResult(
                        title=str(item.get("title", "")),
                        url=str(item.get("url", "")),
                        snippet=str(item.get("content", "")),
                        source="searxng",
                        score=float(item.get("score", 0.0)),
                    )
                )

            LOGGER.debug(
                "SearXNG search completed",
                extra={
                    "event": "searxng_search_done",
                    "extra_fields": {
                        "results_count": len(results),
                        "instance": self._instance_url,
                    },
                },
            )
            return results

        except httpx.ConnectError:
            LOGGER.warning(
                "SearXNG instance unreachable at %s",
                self._instance_url,
                extra={"event": "searxng_connect_error"},
            )
            return []
        except (httpx.HTTPStatusError, httpx.TimeoutException):
            raise
        except Exception:
            LOGGER.warning(
                "SearXNG search failed",
                extra={"event": "searxng_search_error"},
                exc_info=True,
            )
            return []

    async def fetch(self, url: str) -> Document:
        """Fetch a webpage and extract text content.

        Reuses the builtin HTML-to-text extraction logic.
        """
        client = await self._get_client()

        try:
            response = await client.get(url)
            response.raise_for_status()

            raw_html = response.text
            if len(raw_html) > self.MAX_CONTENT_LENGTH:
                raw_html = raw_html[: self.MAX_CONTENT_LENGTH]

            title = _extract_title(raw_html)
            text = _html_to_text(raw_html)

            return Document(url=url, title=title, text=text, html=raw_html)
        except (httpx.HTTPStatusError, httpx.TimeoutException):
            raise
        except Exception as e:
            return Document(url=url, title="", text=f"Error fetching URL: {e}")

    async def healthcheck(self) -> ProviderStatus:
        """Check if the SearXNG instance is reachable."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self._instance_url}/search",
                params={"q": "test", "format": "json"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return ProviderStatus.OK
            return ProviderStatus.ERROR
        except httpx.ConnectError:
            return ProviderStatus.UNAVAILABLE
        except httpx.TimeoutException:
            return ProviderStatus.TIMEOUT
        except Exception:
            return ProviderStatus.ERROR

    def capabilities(self) -> set[str]:
        """SearXNG supports both search and URL extraction."""
        return {"web_search", "url_extract"}

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
