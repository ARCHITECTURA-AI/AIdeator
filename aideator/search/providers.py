"""Search provider interface and base types.

Defines the SearchResult data class and SearchProvider abstract base class
that all search implementations must follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderStatus(Enum):
    """Health check status for search providers."""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True)
class SearchResult:
    """Standardized search result.

    Attributes:
        title: Result title
        url: Source URL
        snippet: Text excerpt / summary
        source: Provider that returned this result (e.g. 'tavily', 'builtin')
        score: Relevance score (0.0 to 1.0, provider-dependent)
    """

    title: str
    url: str
    snippet: str
    source: str = ""
    score: float = 0.0


@dataclass(frozen=True)
class Document:
    """Fetched document content.

    Attributes:
        url: Original URL
        title: Page title (if extractable)
        text: Extracted plain text content
        html: Raw HTML (optional, for downstream processing)
    """

    url: str
    title: str = ""
    text: str = ""
    html: str = ""


class SearchProvider(ABC):
    """Abstract base class for search providers.

    All search providers must implement:
    - search(): Perform a web search query
    - fetch(): Fetch and extract content from a URL
    - healthcheck(): Check provider availability
    - capabilities(): Report what this provider can do
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        mode: str = "general",
    ) -> list[SearchResult]:
        """Search for results matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results
            mode: Search mode (general, research, news, etc.)

        Returns:
            List of SearchResult objects
        """
        ...

    @abstractmethod
    async def fetch(self, url: str) -> Document:
        """Fetch and extract content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Document with extracted text content
        """
        ...

    @abstractmethod
    async def healthcheck(self) -> ProviderStatus:
        """Check if the provider is healthy and available.

        Returns:
            ProviderStatus indicating health state
        """
        ...

    @abstractmethod
    def capabilities(self) -> set[str]:
        """Report the capabilities of this provider.

        Possible capabilities:
        - 'web_search': Can perform web searches
        - 'url_extract': Can fetch and extract URL content

        Returns:
            Set of capability strings
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key to function."""
        ...

    async def close(self) -> None:
        """Clean up any resources (HTTP clients, etc.)."""

    async def __aenter__(self) -> SearchProvider:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
