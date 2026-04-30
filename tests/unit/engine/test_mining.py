"""Unit tests for complaint mining logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aideator.search.providers import SearchResult
from engine.signal_collector import build_complaint_queries, collect_search_signals


def test_build_complaint_queries() -> None:
    """Test that complaint queries are correctly formatted."""
    queries = build_complaint_queries("AI Tool", "A tool for developers to code faster")
    assert any("site:reddit.com" in q for q in queries)
    assert any("1 star" in q for q in queries)
    # Check topic injection (title + first 3 words of description)
    assert all("AI Tool A tool for" in q for q in queries)

@pytest.mark.asyncio
async def test_collect_search_signals_deep_deduplication() -> None:
    """Test that deep search deduplicates results by URL."""
    mock_results_1 = [SearchResult(title="R1", url="https://e1.com", snippet="s1", source="s")]
    mock_results_2 = [
        SearchResult(title="R1-duplicate", url="https://e1.com", snippet="s1-dup", source="s")
    ]
    mock_results_3 = [
        SearchResult(title="R2-unique", url="https://e2.com", snippet="s2", source="s")
    ]
    
    mock_provider = MagicMock()
    mock_provider.name = "mock"
    mock_provider.capabilities.return_value = {"web_search"}
    # First call is general, subsequent are mining
    mock_provider.search = AsyncMock(
        side_effect=[mock_results_1, mock_results_2, mock_results_3, [], []]
    )
    
    with patch("aideator.search.registry.get_search_provider", return_value=mock_provider):
        results = await collect_search_signals(
            mode="cloud-enabled",
            title="T",
            description="D",
            deep_search=True
        )
        
    # Should have R1 and R2, but not the duplicate R1
    urls = [r.url for r in results]
    assert len(urls) == 2
    assert "https://e1.com" in urls
    assert "https://e2.com" in urls
