"""DuckDuckGo search provider — free tier, no API key.

Uses the ddgs library for zero-cost web search.
Queries go to DuckDuckGo servers, so this provider is
skipped in local-only mode (same as any search provider).

Rate-limit and error handling is built-in: failures
are caught and return empty results, never crash a run.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from aideator.search.providers import Document, ProviderStatus, SearchProvider, SearchResult

LOGGER = logging.getLogger("aideator.search.duckduckgo")

# Re-use the builtin HTML helpers for fetch()
from aideator.search.builtin import _extract_title, _html_to_text


class DuckDuckGoSearchProvider(SearchProvider):
    """Free search provider using DuckDuckGo.

    Zero cost, zero config.  Best for personal / hobby use,
    development, and testing.

    Capabilities:
    - web_search: Real web search via DuckDuckGo
    - url_extract: URL content extraction (reuses builtin logic)
    """

    DEFAULT_TIMEOUT = 20.0
    MAX_CONTENT_LENGTH = 1_000_000  # 1 MB

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for fetch() operations."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; AIdeator/1.0; "
                        "+https://github.com/ARCHITECTURA-AI/AIdeator)"
                    ),
                    "Accept": "text/html,application/xhtml+xml,text/plain",
                },
            )
        return self._client

    # ------------------------------------------------------------------ #
    # SearchProvider interface
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        return "duckduckgo"

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
        """Search using DuckDuckGo via the ddgs library.

        The ddgs library is synchronous, so we run it in a
        thread pool to avoid blocking the async event loop.

        Args:
            query: Search query string
            limit: Maximum results (capped at 20)
            mode: Ignored (DuckDuckGo has no mode variant)

        Returns:
            List of SearchResult objects (empty on error/rate-limit)
        """
        if not query or not query.strip():
            return []

        effective_limit = min(limit, 20)

        try:
            raw_results = await asyncio.to_thread(
                self._search_sync, query, effective_limit
            )
        except Exception:
            LOGGER.warning(
                "DuckDuckGo search failed",
                extra={"event": "ddg_search_error"},
                exc_info=True,
            )
            return []

        results: list[SearchResult] = []
        for item in raw_results:
            results.append(
                SearchResult(
                    title=str(item.get("title", "")),
                    url=str(item.get("href", item.get("link", ""))),
                    snippet=str(item.get("body", item.get("snippet", ""))),
                    source="duckduckgo",
                    score=0.0,  # DuckDuckGo doesn't provide relevance scores
                )
            )

        LOGGER.debug(
            "DuckDuckGo search completed",
            extra={
                "event": "ddg_search_done",
                "extra_fields": {"results_count": len(results)},
            },
        )
        return results

    @staticmethod
    def _search_sync(query: str, max_results: int) -> list[dict[str, Any]]:
        """Synchronous DuckDuckGo search (runs in thread pool).

        Handles import errors and rate-limit exceptions gracefully.
        """
        try:
            from ddgs import DDGS
        except ImportError:
            LOGGER.error(
                "ddgs package not installed. Install with: pip install ddgs",
                extra={"event": "ddg_import_error"},
            )
            return []

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return results
        except Exception as exc:
            # Catch RatelimitException and any other ddgs errors
            exc_name = type(exc).__name__
            LOGGER.warning(
                "DuckDuckGo search error: %s: %s",
                exc_name,
                str(exc)[:200],
                extra={"event": "ddg_rate_limit"},
            )
            return []

    async def fetch(self, url: str) -> Document:
        """Fetch a webpage and extract text content.

        Reuses the builtin HTML-to-text extraction logic.

        Args:
            url: URL to fetch

        Returns:
            Document with extracted text
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
        """Check if DuckDuckGo search is reachable."""
        try:
            results = await asyncio.to_thread(self._search_sync, "test", 1)
            if results:
                return ProviderStatus.OK
            return ProviderStatus.ERROR
        except Exception:
            return ProviderStatus.ERROR

    def capabilities(self) -> set[str]:
        """DuckDuckGo supports both search and URL extraction."""
        return {"web_search", "url_extract"}

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
