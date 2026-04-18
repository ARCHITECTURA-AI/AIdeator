"""Search provider registry for dynamic provider loading.

Maps provider names to provider classes and handles configuration.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.config import Settings

from aideator.search.providers import SearchProvider


def get_search_provider(settings: Settings | dict[str, str]) -> SearchProvider:
    """Get a search provider instance based on settings.

    Args:
        settings: Settings object or dict with provider configuration.
            Expected keys: search_provider, and provider-specific API keys.

    Returns:
        Configured SearchProvider instance

    Raises:
        ValueError: If provider is not recognized
        ValueError: If required API key is missing for paid providers
    """
    # Handle both Settings object and dict
    if hasattr(settings, "search_provider"):
        provider_name = settings.search_provider
    else:
        provider_name = settings.get("search_provider", "duckduckgo")

    provider_name = provider_name.strip().lower()

    if provider_name == "builtin":
        from aideator.search.builtin import BuiltinSearchProvider

        return BuiltinSearchProvider()

    elif provider_name == "duckduckgo":
        from aideator.search.duckduckgo import DuckDuckGoSearchProvider

        return DuckDuckGoSearchProvider()

    elif provider_name == "searxng":
        from aideator.search.searxng import SearXNGSearchProvider

        # Get instance URL from settings or env
        instance_url = None
        if hasattr(settings, "searxng_instance_url"):
            instance_url = settings.searxng_instance_url
        
        if not instance_url:
            instance_url = os.getenv("SEARXNG_URL")
            
        if not instance_url and isinstance(settings, dict):
            instance_url = settings.get("searxng_instance_url")

        if not instance_url:
            raise ValueError(
                "SearXNG search provider requires an instance URL. "
                "Set SEARXNG_URL environment variable or configure "
                "searxng_instance_url in your config file."
            )
        return SearXNGSearchProvider(instance_url=instance_url)

    elif provider_name == "tavily":
        from aideator.search.tavily import TavilySearchProvider

        # Get API key
        if hasattr(settings, "get_effective_search_api_key"):
            api_key = settings.get_effective_search_api_key()
        elif hasattr(settings, "tavily_api_key"):
            api_key = settings.tavily_api_key
        else:
            tavily_env = settings.get("tavily_api_key_env", "TAVILY_API_KEY")
            api_key = os.getenv(tavily_env, settings.get("search_api_key", ""))

        if not api_key:
            raise ValueError(
                "Tavily search provider requires an API key. "
                "Set TAVILY_API_KEY environment variable or configure "
                "tavily_api_key_env in config file."
            )
        return TavilySearchProvider(api_key=api_key)

    elif provider_name == "exa":
        from aideator.search.exa import ExaSearchProvider

        # Get API key
        if hasattr(settings, "get_effective_search_api_key"):
            api_key = settings.get_effective_search_api_key()
        else:
            exa_env = settings.get("exa_api_key_env", "EXA_API_KEY")
            api_key = os.getenv(exa_env, settings.get("search_api_key", ""))

        if not api_key:
            raise ValueError(
                "Exa search provider requires an API key. "
                "Set EXA_API_KEY environment variable or configure "
                "exa_api_key_env in config file."
            )
        return ExaSearchProvider(api_key=api_key)

    else:
        available = "builtin, duckduckgo, searxng, tavily, exa"
        raise ValueError(
            f"Unknown search provider: '{provider_name}'. "
            f"Available providers: {available}"
        )


def list_available_search_providers() -> list[dict[str, str | bool]]:
    """List all available search providers with metadata.

    Providers are listed in recommended order (free → paid).

    Returns:
        List of provider info dictionaries
    """
    return [
        {
            "name": "duckduckgo",
            "display_name": "DuckDuckGo",
            "description": "Free web search, no API key needed (recommended default)",
            "requires_api_key": False,
            "tier": "free",
            "capabilities": "web_search, url_extract",
        },
        {
            "name": "tavily",
            "display_name": "Tavily",
            "description": "AI-powered web search (paid, higher quality)",
            "requires_api_key": True,
            "tier": "mid",
            "capabilities": "web_search, url_extract",
        },
        {
            "name": "exa",
            "display_name": "Exa",
            "description": "AI-native semantic search (paid, best for research)",
            "requires_api_key": True,
            "tier": "high",
            "capabilities": "web_search, url_extract",
        },
        {
            "name": "searxng",
            "display_name": "SearXNG",
            "description": "Self-hosted metasearch (requires running SearXNG instance)",
            "requires_api_key": False,
            "tier": "self-hosted",
            "capabilities": "web_search, url_extract",
        },
        {
            "name": "builtin",
            "display_name": "Built-in (Offline)",
            "description": "URL extraction only, no web search (for local-only mode)",
            "requires_api_key": False,
            "tier": "offline",
            "capabilities": "url_extract",
        },
    ]
