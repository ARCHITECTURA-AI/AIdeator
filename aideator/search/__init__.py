"""Search provider abstraction for AIdeator.

Provides a unified interface for web search across multiple providers:
- DuckDuckGoSearchProvider: Free web search, no API key (recommended default)
- TavilySearchProvider: AI-powered search (paid, mid-tier)
- ExaSearchProvider: AI-native semantic search (paid, high-tier)
- SearXNGSearchProvider: Self-hosted metasearch (your infrastructure)
- BuiltinSearchProvider: URL extraction only, no web search (offline fallback)
"""

from aideator.search.providers import ProviderStatus, SearchProvider, SearchResult
from aideator.search.registry import get_search_provider

__all__ = [
    "SearchProvider",
    "SearchResult",
    "ProviderStatus",
    "get_search_provider",
]
