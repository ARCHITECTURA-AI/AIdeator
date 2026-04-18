"""Unit tests for signal collector with search registry integration."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from engine.signal_collector import (
    build_external_payload,
    build_hybrid_query,
    collect_search_signals,
    collect_search_signals_sync,
)


class TestBuildHybridQuery:
    """Tests for keyword truncation."""

    def test_truncates_to_10_words(self) -> None:
        text = " ".join(f"word{i}" for i in range(20))
        result = build_hybrid_query(text)
        assert len(result.split()) == 10

    def test_short_text_unchanged(self) -> None:
        result = build_hybrid_query("hello world")
        assert result == "hello world"

    def test_empty_text(self) -> None:
        result = build_hybrid_query("")
        assert result == ""

    def test_strips_whitespace(self) -> None:
        result = build_hybrid_query("  a  b  c  ")
        assert result == "a b c"


class TestBuildExternalPayload:
    """Tests for mode-dependent payload construction."""

    def test_local_only_returns_empty(self) -> None:
        result = build_external_payload(mode="local-only", title="T", description="D")
        assert result == {"query": ""}

    def test_hybrid_truncates(self) -> None:
        long_desc = " ".join(f"word{i}" for i in range(30))
        result = build_external_payload(mode="hybrid", title="Title", description=long_desc)
        assert len(result["query"].split()) == 10

    def test_cloud_enabled_full_query(self) -> None:
        result = build_external_payload(
            mode="cloud-enabled", title="My Title", description="My Description"
        )
        assert result["query"] == "My Title My Description"


class TestCollectSearchSignals:
    """Tests for async search signal collection."""

    def test_local_only_returns_empty(self) -> None:
        results = asyncio.run(
            collect_search_signals(mode="local-only", title="T", description="D")
        )
        assert results == []

    def test_empty_query_returns_empty(self) -> None:
        results = asyncio.run(
            collect_search_signals(mode="local-only", title="", description="")
        )
        assert results == []


class TestCollectSearchSignalsSync:
    """Tests for sync wrapper."""

    def test_local_only_sync(self) -> None:
        results = collect_search_signals_sync(
            mode="local-only", title="T", description="D"
        )
        assert results == []

    def test_hybrid_with_builtin_provider_returns_empty(self) -> None:
        """Builtin provider doesn't support web_search, should return empty."""
        from aideator.search.builtin import BuiltinSearchProvider

        with patch(
            "aideator.search.registry.get_search_provider",
            return_value=BuiltinSearchProvider(),
        ):
            results = collect_search_signals_sync(
                mode="hybrid", title="AI tool", description="for developers"
            )
        assert results == []

    def test_hybrid_with_mocked_duckduckgo_returns_results(self) -> None:
        """DuckDuckGo provider supports web_search, should return results."""
        from aideator.search.providers import SearchResult

        mock_provider = MagicMock()
        mock_provider.name = "duckduckgo"
        mock_provider.capabilities.return_value = {"web_search", "url_extract"}
        mock_provider.search = AsyncMock(
            return_value=[
                SearchResult(title="R1", url="https://e.com", snippet="s", source="duckduckgo"),
            ]
        )

        with patch(
            "aideator.search.registry.get_search_provider",
            return_value=mock_provider,
        ):
            results = collect_search_signals_sync(
                mode="hybrid", title="AI tool", description="for developers"
            )
        assert len(results) == 1
        assert results[0].source == "duckduckgo"
