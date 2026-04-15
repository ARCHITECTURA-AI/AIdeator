"""Unit tests for search provider registry."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from aideator.search.registry import get_search_provider, list_available_search_providers


class TestGetSearchProvider:
    """Tests for get_search_provider registry function."""

    def test_builtin_from_dict(self) -> None:
        from aideator.search.builtin import BuiltinSearchProvider

        provider = get_search_provider({"search_provider": "builtin"})
        assert isinstance(provider, BuiltinSearchProvider)

    def test_builtin_default(self) -> None:
        from aideator.search.duckduckgo import DuckDuckGoSearchProvider

        provider = get_search_provider({})
        assert isinstance(provider, DuckDuckGoSearchProvider)

    def test_tavily_with_key(self) -> None:
        from aideator.search.tavily import TavilySearchProvider

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key-123"}):
            provider = get_search_provider({"search_provider": "tavily"})
            assert isinstance(provider, TavilySearchProvider)

    def test_tavily_missing_key_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Tavily"):
                get_search_provider({"search_provider": "tavily"})

    def test_exa_with_key(self) -> None:
        from aideator.search.exa import ExaSearchProvider

        with patch.dict(os.environ, {"EXA_API_KEY": "test-exa-key"}):
            provider = get_search_provider({"search_provider": "exa"})
            assert isinstance(provider, ExaSearchProvider)

    def test_exa_missing_key_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Exa"):
                get_search_provider({"search_provider": "exa"})

    def test_invalid_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown search provider"):
            get_search_provider({"search_provider": "nosuch"})

    def test_case_insensitive(self) -> None:
        from aideator.search.builtin import BuiltinSearchProvider

        provider = get_search_provider({"search_provider": "  Builtin  "})
        assert isinstance(provider, BuiltinSearchProvider)


class TestListAvailableSearchProviders:
    """Tests for listing available search providers."""

    def test_returns_five_providers(self) -> None:
        providers = list_available_search_providers()
        assert len(providers) == 5

    def test_provider_names(self) -> None:
        providers = list_available_search_providers()
        names = {p["name"] for p in providers}
        assert names == {"builtin", "duckduckgo", "searxng", "tavily", "exa"}

    def test_builtin_no_key_required(self) -> None:
        providers = list_available_search_providers()
        builtin = [p for p in providers if p["name"] == "builtin"][0]
        assert builtin["requires_api_key"] is False

    def test_paid_providers_require_key(self) -> None:
        providers = list_available_search_providers()
        for provider in providers:
            if provider["name"] in ("tavily", "exa"):
                assert provider["requires_api_key"] is True
