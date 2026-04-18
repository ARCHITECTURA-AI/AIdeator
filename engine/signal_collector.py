"""Signal payload builders for mode-dependent collection.

Integrates with the search provider registry to dispatch queries
to the configured search provider based on the run mode.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aideator.search.providers import SearchResult

LOGGER = logging.getLogger("engine.signal_collector")


def build_hybrid_query(text: str) -> str:
    """Build a privacy-safe hybrid query (truncated to 10 words)."""
    words = [word for word in text.split() if word.strip()]
    return " ".join(words[:10])


def build_external_payload(*, mode: str, title: str, description: str) -> dict[str, str]:
    """Build the search query payload for the given mode.

    Args:
        mode: Run mode ('local-only', 'hybrid', 'cloud-enabled')
        title: Idea title
        description: Idea description

    Returns:
        Dict with 'query' key (empty for local-only)
    """
    if mode == "hybrid":
        return {"query": build_hybrid_query(f"{title} {description}")}
    if mode == "cloud-enabled":
        return {"query": f"{title} {description}"}
    return {"query": ""}


async def collect_search_signals(
    *,
    mode: str,
    title: str,
    description: str,
    limit: int = 5,
) -> list[SearchResult]:
    """Collect search signals from the configured provider.

    This is the main integration point between the orchestrator
    and the search provider registry.

    Args:
        mode: Run mode. 'local-only' skips search entirely.
        title: Idea title for query construction.
        description: Idea description for query construction.
        limit: Maximum number of search results.

    Returns:
        List of SearchResult objects (empty for local-only mode).

    Raises:
        No exceptions — failures are logged and return empty list.
    """
    if mode == "local-only":
        LOGGER.debug("Skipping search signals for local-only mode")
        return []

    payload = build_external_payload(mode=mode, title=title, description=description)
    query = payload.get("query", "")
    if not query:
        return []

    try:
        from aideator.search.registry import get_search_provider
        from api.config import settings

        provider = get_search_provider(settings)

        LOGGER.info(
            "Collecting search signals",
            extra={
                "event": "search_signals_start",
                "extra_fields": {
                    "provider": provider.name,
                    "mode": mode,
                    "query_len": len(query),
                },
            },
        )

        # Check if provider supports web search
        caps = provider.capabilities()
        if "web_search" not in caps:
            LOGGER.debug(
                "Provider %s does not support web_search, skipping", provider.name
            )
            return []

        results = await provider.search(query, limit=limit, mode="general")

        # --- CIRCUIT BREAKER / FAILOVER LOGIC ---
        if not results and provider.name != "duckduckgo" and provider.name != "builtin":
            LOGGER.info(
                "Primary search provider returned no results, attempting failover",
                extra={
                    "event": "search_failover",
                    "extra_fields": {
                        "from_provider": provider.name,
                        "to_provider": "duckduckgo",
                    },
                },
            )
            try:
                # Fallback to duckduckgo
                fallback_settings = {"search_provider": "duckduckgo"}
                fallback_provider = get_search_provider(fallback_settings)
                results = await fallback_provider.search(query, limit=limit, mode="general")
                
                LOGGER.info(
                    "Search failover successful",
                    extra={
                        "event": "search_signals_done",
                        "extra_fields": {
                            "provider": "duckduckgo",
                            "results_count": len(results),
                            "is_fallback": True,
                        },
                    },
                )
            except Exception as e:
                LOGGER.warning(f"Search failover to DuckDuckGo failed: {e}")
        else:
            LOGGER.info(
                "Search signals collected",
                extra={
                    "event": "search_signals_done",
                    "extra_fields": {
                        "provider": provider.name,
                        "results_count": len(results),
                    },
                },
            )

        return results

    except Exception:
        LOGGER.warning(
            "Search signal collection failed",
            extra={"event": "search_signals_error"},
            exc_info=True,
        )
        return []


def collect_search_signals_sync(
    *,
    mode: str,
    title: str,
    description: str,
    limit: int = 5,
) -> list[SearchResult]:
    """Synchronous wrapper for collect_search_signals.

    Used by the orchestrator which currently runs synchronously.
    Creates or reuses an event loop for the async search call.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an async context — can't use asyncio.run
        # Fall back to empty results to avoid deadlock
        LOGGER.debug("Already in async context, skipping sync search wrapper")
        return []

    return asyncio.run(
        collect_search_signals(
            mode=mode,
            title=title,
            description=description,
            limit=limit,
        )
    )
