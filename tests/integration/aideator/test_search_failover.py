from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aideator.search.providers import SearchResult
from engine.signal_collector import collect_search_signals


@pytest.mark.asyncio
async def test_failover_from_tavily_to_duckduckgo_on_ratelimit():
    """TC-I-330: System fails over to DDG when Tavily is rate-limited."""
    
    # Mock primary provider (Tavily) that returns empty results
    mock_tavily = MagicMock()
    mock_tavily.name = "tavily"
    mock_tavily.capabilities.return_value = {"web_search"}
    mock_tavily.search = AsyncMock(return_value=[]) 
    
    # Mock fallback provider (DuckDuckGo)
    mock_ddg = MagicMock()
    mock_ddg.name = "duckduckgo"
    mock_ddg.capabilities.return_value = {"web_search"}
    mock_ddg.search = AsyncMock(return_value=[
        SearchResult(
            title="DDG Result",
            url="http://ddg.com",
            snippet="Fallback success!",
            source="duckduckgo"
        )
    ])
    
    # Patch get_search_provider
    with patch("aideator.search.registry.get_search_provider") as mock_get_provider:
        # First call returns tavily, second call returns ddg (called inside fallback logic)
        mock_get_provider.side_effect = [mock_tavily, mock_ddg]
        
        with patch("engine.signal_collector.LOGGER") as mock_logger:
            results = await collect_search_signals(
                mode="cloud-enabled", 
                title="Test", 
                description="Test"
            )
            
            # Assertions
            assert len(results) == 1
            assert results[0].title == "DDG Result"
            assert results[0].source == "duckduckgo"
            
            # Verify failover log (logged as INFO in signal_collector.py)
            failover_logged = any(
                "search_failover" == call.kwargs.get("extra", {}).get("event")
                for call in mock_logger.info.call_args_list
            )
            assert failover_logged, "Search failover event not logged in INFO"

@pytest.mark.asyncio
async def test_no_failover_if_results_found():
    """TC-I-333: No failover occurs if primary provider succeeds."""
    mock_tavily = MagicMock()
    mock_tavily.name = "tavily"
    mock_tavily.capabilities.return_value = {"web_search"}
    mock_tavily.search = AsyncMock(return_value=[
        SearchResult(
            title="Tavily Result",
            url="http://tavily.com",
            snippet="Primary success!",
            source="tavily"
        )
    ])

    # We also need to make sure get_search_provider is only called once
    registry_path = "aideator.search.registry.get_search_provider"
    with patch(registry_path, return_value=mock_tavily) as mock_get:
            results = await collect_search_signals(
                mode="cloud-enabled", 
                title="Test", 
                description="Test"
            )
            assert len(results) == 1
            assert results[0].title == "Tavily Result"
            assert results[0].source == "tavily"
            assert mock_get.call_count == 1
