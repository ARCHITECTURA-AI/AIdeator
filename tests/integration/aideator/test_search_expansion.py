import argparse
import io
from contextlib import redirect_stdout
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aideator.cli import command_config_show
from aideator.search.providers import ProviderStatus
from aideator.search.registry import get_search_provider
from engine.signal_collector import collect_search_signals


@pytest.mark.asyncio
async def test_searxng_connectivity_failure_handled_gracefully():
    """TC-I-311: SignalCollector handles SearXNG failures without raising."""
    with patch("aideator.search.registry.get_search_provider") as mock_reg:
        mock_provider = MagicMock()
        mock_provider.name = "searxng"
        mock_provider.capabilities.return_value = {"web_search"}
        mock_provider.search = AsyncMock(side_effect=Exception("Connect error"))
        mock_reg.return_value = mock_provider
        
        results = await collect_search_signals(
            mode="cloud-enabled", 
            title="Test", 
            description="Test"
        )
        assert results == []

@pytest.mark.asyncio
async def test_duckduckgo_rate_limit_logged_specifically():
    """TC-I-312: DuckDuckGo rate limit logs a specific event."""
    from aideator.search.duckduckgo import DuckDuckGoSearchProvider
    provider = DuckDuckGoSearchProvider()
    
    with patch("aideator.search.duckduckgo.HAS_DDGS", True):
        # We need to mock DDGS in the module where it's imported
        with patch("aideator.search.duckduckgo.DDGS") as mock_ddgs:
            mock_instance = mock_ddgs.return_value.__enter__.return_value
            # Use "Ratelimit" to trigger our custom logic in duckduckgo.py
            mock_instance.text.side_effect = Exception("Ratelimit query error")
            
            with patch("aideator.search.duckduckgo.LOGGER") as mock_logger:
                results = await provider.search("test")
                assert results == []
                
                found = False
                for call in mock_logger.warning.call_args_list:
                    msg = str(call[0][0]).lower() if call[0] else ""
                    is_rl = "rate limit" in msg
                    is_ev = call.kwargs.get("extra", {}).get("event") == "ddg_rate_limit"
                    if is_rl or is_ev:
                        found = True
                        break
                assert found, "Rate limit event not logged"

def test_registry_validates_searxng_config():
    """TC-I-313: get_search_provider validates mandatory configuration."""
    settings = {"search_provider": "searxng"}
    with pytest.raises(ValueError, match="SearXNG search provider requires an instance URL"):
        get_search_provider(settings)

def test_config_show_displays_health_status():
    """TC-I-310: aideator config show displays search health status."""
    args = argparse.Namespace()
    
    # Use a real async function instead of AsyncMock for stability in asyncio.run
    async def mock_health():
        return ProviderStatus.OK

    mock_provider = MagicMock()
    mock_provider.name = "mock-search"
    mock_provider.healthcheck = mock_health

    f = io.StringIO()
    with redirect_stdout(f):
        with patch("aideator.cli.get_search_provider", return_value=mock_provider):
             command_config_show(args)
             
    output = f.getvalue()
    assert "Selected: mock-search" in output
    assert "[HEALTHY]" in output
