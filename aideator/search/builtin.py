"""Built-in search provider for zero-budget users.

Provides basic webpage fetching and text extraction without any
external API keys. Uses httpx for HTTP requests and a simple
HTML-to-text extractor.
"""

from __future__ import annotations

import re
from html import unescape
from typing import Any

import httpx

from aideator.search.providers import Document, ProviderStatus, SearchProvider, SearchResult

# Simple HTML tag stripper (no external dependency required)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript)[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)


def _extract_title(html: str) -> str:
    """Extract <title> content from HTML."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        return unescape(match.group(1)).strip()
    return ""


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text by stripping tags.

    This is a lightweight extractor that:
    1. Removes <script>, <style>, <noscript> blocks
    2. Strips remaining HTML tags
    3. Unescapes HTML entities
    4. Normalizes whitespace
    """
    text = _SCRIPT_STYLE_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", text)
    text = unescape(text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


class BuiltinSearchProvider(SearchProvider):
    """Built-in provider with basic webpage fetching.

    Capabilities:
    - url_extract: Fetch and extract text from any public URL

    Does NOT perform web search queries (no search engine API).
    Returns empty results for search() calls.
    """

    DEFAULT_TIMEOUT = 15.0
    MAX_CONTENT_LENGTH = 1_000_000  # 1MB max download

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
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
                    "Accept": "text/html,application/xhtml+xml,text/plain",
                },
            )
        return self._client

    @property
    def name(self) -> str:
        return "builtin"

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
        """Builtin provider cannot perform web search.

        Returns an empty list. Use fetch() to extract content from known URLs.
        """
        return []

    async def fetch(self, url: str) -> Document:
        """Fetch a webpage and extract text content.

        Args:
            url: URL to fetch

        Returns:
            Document with extracted text

        Raises:
            httpx.HTTPStatusError: On non-2xx responses
            httpx.TimeoutException: On timeout
        """
        client = await self._get_client()

        try:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            raw_html = response.text

            # Limit content length
            if len(raw_html) > self.MAX_CONTENT_LENGTH:
                raw_html = raw_html[: self.MAX_CONTENT_LENGTH]

            title = _extract_title(raw_html)
            text = _html_to_text(raw_html)

            return Document(
                url=url,
                title=title,
                text=text,
                html=raw_html,
            )
        except httpx.HTTPStatusError:
            raise
        except httpx.TimeoutException:
            raise
        except Exception as e:
            return Document(url=url, title="", text=f"Error fetching URL: {e}")

    async def healthcheck(self) -> ProviderStatus:
        """Builtin provider is always available."""
        return ProviderStatus.OK

    def capabilities(self) -> set[str]:
        """Builtin supports URL extraction only."""
        return {"url_extract"}

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
