"""Unit tests for search provider interface and implementations."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from aideator.search.providers import Document, ProviderStatus, SearchProvider, SearchResult


class TestSearchResult:
    """Tests for SearchResult data class."""

    def test_create_minimal(self) -> None:
        r = SearchResult(title="Test", url="https://example.com", snippet="snippet")
        assert r.title == "Test"
        assert r.url == "https://example.com"
        assert r.snippet == "snippet"
        assert r.source == ""
        assert r.score == 0.0

    def test_create_full(self) -> None:
        r = SearchResult(
            title="Full", url="https://ex.com", snippet="s", source="tavily", score=0.95
        )
        assert r.source == "tavily"
        assert r.score == 0.95

    def test_frozen(self) -> None:
        r = SearchResult(title="T", url="u", snippet="s")
        with pytest.raises(AttributeError):
            r.title = "changed"  # type: ignore[misc]


class TestDocument:
    """Tests for Document data class."""

    def test_create_minimal(self) -> None:
        d = Document(url="https://example.com")
        assert d.url == "https://example.com"
        assert d.title == ""
        assert d.text == ""
        assert d.html == ""


class TestProviderStatus:
    """Tests for ProviderStatus enum."""

    def test_all_values(self) -> None:
        assert ProviderStatus.OK.value == "ok"
        assert ProviderStatus.ERROR.value == "error"
        assert ProviderStatus.TIMEOUT.value == "timeout"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"
        assert ProviderStatus.NOT_CONFIGURED.value == "not_configured"


class TestBuiltinSearchProvider:
    """Tests for BuiltinSearchProvider."""

    def test_returns_empty_search(self) -> None:
        from aideator.search.builtin import BuiltinSearchProvider

        provider = BuiltinSearchProvider()
        results = asyncio.run(provider.search("test query"))
        assert results == []

    def test_capabilities(self) -> None:
        from aideator.search.builtin import BuiltinSearchProvider

        provider = BuiltinSearchProvider()
        caps = provider.capabilities()
        assert "url_extract" in caps
        assert "web_search" not in caps

    def test_name(self) -> None:
        from aideator.search.builtin import BuiltinSearchProvider

        provider = BuiltinSearchProvider()
        assert provider.name == "builtin"

    def test_no_api_key_required(self) -> None:
        from aideator.search.builtin import BuiltinSearchProvider

        provider = BuiltinSearchProvider()
        assert provider.requires_api_key is False

    def test_healthcheck_always_ok(self) -> None:
        from aideator.search.builtin import BuiltinSearchProvider

        provider = BuiltinSearchProvider()
        status = asyncio.run(provider.healthcheck())
        assert status == ProviderStatus.OK


class TestBuiltinHtmlToText:
    """Tests for the built-in HTML-to-text extractor."""

    def test_strips_tags(self) -> None:
        from aideator.search.builtin import _html_to_text

        assert "Hello" in _html_to_text("<p>Hello</p>")

    def test_strips_scripts(self) -> None:
        from aideator.search.builtin import _html_to_text

        html = "<p>Before</p><script>alert('x')</script><p>After</p>"
        text = _html_to_text(html)
        assert "alert" not in text
        assert "Before" in text
        assert "After" in text

    def test_extracts_title(self) -> None:
        from aideator.search.builtin import _extract_title

        assert _extract_title("<html><title>My Page</title></html>") == "My Page"

    def test_extracts_title_empty(self) -> None:
        from aideator.search.builtin import _extract_title

        assert _extract_title("<html><body></body></html>") == ""


class TestTavilySearchProvider:
    """Tests for TavilySearchProvider configuration."""

    def test_name(self) -> None:
        from aideator.search.tavily import TavilySearchProvider

        provider = TavilySearchProvider(api_key="test-key")
        assert provider.name == "tavily"

    def test_requires_api_key(self) -> None:
        from aideator.search.tavily import TavilySearchProvider

        provider = TavilySearchProvider(api_key="test-key")
        assert provider.requires_api_key is True

    def test_capabilities(self) -> None:
        from aideator.search.tavily import TavilySearchProvider

        provider = TavilySearchProvider(api_key="test-key")
        caps = provider.capabilities()
        assert "web_search" in caps
        assert "url_extract" in caps

    def test_healthcheck_not_configured(self) -> None:
        from aideator.search.tavily import TavilySearchProvider

        provider = TavilySearchProvider(api_key="")
        status = asyncio.run(provider.healthcheck())
        assert status == ProviderStatus.NOT_CONFIGURED

    def test_search_empty_with_no_key(self) -> None:
        from aideator.search.tavily import TavilySearchProvider

        provider = TavilySearchProvider(api_key="")
        results = asyncio.run(provider.search("test"))
        assert results == []


class TestExaSearchProvider:
    """Tests for ExaSearchProvider configuration."""

    def test_name(self) -> None:
        from aideator.search.exa import ExaSearchProvider

        provider = ExaSearchProvider(api_key="test-key")
        assert provider.name == "exa"

    def test_requires_api_key(self) -> None:
        from aideator.search.exa import ExaSearchProvider

        provider = ExaSearchProvider(api_key="test-key")
        assert provider.requires_api_key is True

    def test_capabilities(self) -> None:
        from aideator.search.exa import ExaSearchProvider

        provider = ExaSearchProvider(api_key="test-key")
        caps = provider.capabilities()
        assert "web_search" in caps
        assert "url_extract" in caps

    def test_healthcheck_not_configured(self) -> None:
        from aideator.search.exa import ExaSearchProvider

        provider = ExaSearchProvider(api_key="")
        status = asyncio.run(provider.healthcheck())
        assert status == ProviderStatus.NOT_CONFIGURED

    def test_search_empty_with_no_key(self) -> None:
        from aideator.search.exa import ExaSearchProvider

        provider = ExaSearchProvider(api_key="")
        results = asyncio.run(provider.search("test"))
        assert results == []
