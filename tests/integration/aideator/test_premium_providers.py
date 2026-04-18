from unittest.mock import MagicMock, patch

import httpx
import pytest

from aideator.search.exa import ExaSearchProvider
from aideator.search.providers import ProviderStatus
from aideator.search.tavily import TavilySearchProvider


@pytest.mark.asyncio
async def test_tavily_rate_limit_handled_and_logged():
    """TC-I-320: Tavily 429 rate limit is caught and logged."""
    provider = TavilySearchProvider(api_key="fake-key")
    
    # Mock httpx response with 429
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limit", request=MagicMock(), response=mock_resp
    )
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        # Patch the module-level LOGGER
        with patch("aideator.search.tavily.LOGGER") as mock_logger:
            results = await provider.search("test")
            assert results == []
            
            found = False
            for call in mock_logger.warning.call_args_list:
                # We check for the 'event' extra or the message
                if "tavily_rate_limit" in str(call) or "rate limit" in str(call).lower():
                    found = True
            assert found, "Tavily rate limit event not logged"

@pytest.mark.asyncio
async def test_exa_rate_limit_handled_and_logged():
    """TC-I-321: Exa 429 rate limit is caught and logged."""
    provider = ExaSearchProvider(api_key="fake-key")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limit", request=MagicMock(), response=mock_resp
    )
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        # Patch the module-level LOGGER
        with patch("aideator.search.exa.LOGGER") as mock_logger:
            results = await provider.search("test")
            assert results == []
            
            found = False
            for call in mock_logger.warning.call_args_list:
                if "exa_rate_limit" in str(call) or "rate limit" in str(call).lower():
                    found = True
            assert found, "Exa rate limit event not logged"

@pytest.mark.asyncio
async def test_premium_healthcheck_reports_ratelimit():
    """TC-I-322: Healthcheck reports RATELIMIT status for 429 responses."""
    tavily = TavilySearchProvider(api_key="fake-key")
    exa = ExaSearchProvider(api_key="fake-key")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        tavily_status = await tavily.healthcheck()
        exa_status = await exa.healthcheck()
        
        assert tavily_status == ProviderStatus.RATELIMIT
        assert exa_status == ProviderStatus.RATELIMIT
