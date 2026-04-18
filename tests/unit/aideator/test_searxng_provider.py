"""Unit tests for SearXNG search provider."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from aideator.search.providers import ProviderStatus, SearchResult


class TestSearXNGProvider:
    """Tests for SearXNGSearchProvider."""

    def _make_provider(self, url: str = "http://localhost:8888"):
        from aideator.search.searxng import SearXNGSearchProvider
        return SearXNGSearchProvider(instance_url=url)

    # ------------------------------------------------------------------ #
    # Contract tests
    # ------------------------------------------------------------------ #

    def test_name(self) -> None:
        provider = self._make_provider()
        assert provider.name == "searxng"

    def test_requires_api_key_false(self) -> None:
        provider = self._make_provider()
        assert provider.requires_api_key is False

    def test_capabilities_include_web_search(self) -> None:
        provider = self._make_provider()
        caps = provider.capabilities()
        assert "web_search" in caps
        assert "url_extract" in caps

    def test_custom_instance_url(self) -> None:
        provider = self._make_provider("http://my-searxng:9090")
        assert provider._instance_url == "http://my-searxng:9090"

    def test_trailing_slash_stripped(self) -> None:
        provider = self._make_provider("http://my-searxng:9090/")
        assert provider._instance_url == "http://my-searxng:9090"

    # ------------------------------------------------------------------ #
    # search() tests
    # ------------------------------------------------------------------ #

    def test_search_empty_query_returns_empty(self) -> None:
        provider = self._make_provider()
        results = asyncio.run(provider.search(""))
        assert results == []

    def test_search_maps_json_api_response(self) -> None:
        """Verify SearXNG JSON API results are correctly mapped."""
        import httpx
        provider = self._make_provider()

        fake_response_data = {
            "results": [
                {
                    "title": "SearXNG Result",
                    "url": "https://example.com/searxng",
                    "content": "Found via SearXNG metasearch.",
                    "score": 0.85,
                },
                {
                    "title": "Second Result",
                    "url": "https://example.com/second",
                    "content": "Another result.",
                    "score": 0.65,
                },
            ]
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = fake_response_data
        mock_response.raise_for_status = MagicMock()

        async def mock_get(url, **kwargs):
            return mock_response

        with patch.object(provider, "_get_client") as mock_client:
            client_instance = MagicMock()
            client_instance.get = mock_get
            mock_client.return_value = client_instance

            results = asyncio.run(provider.search("test query", limit=5))

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "SearXNG Result"
        assert results[0].url == "https://example.com/searxng"
        assert results[0].snippet == "Found via SearXNG metasearch."
        assert results[0].source == "searxng"
        assert results[0].score == 0.85

    def test_search_respects_limit(self) -> None:
        """Verify results are truncated to limit."""
        import httpx
        provider = self._make_provider()

        fake_data = {
            "results": [
                {"title": f"R{i}", "url": f"https://e.com/{i}", "content": f"c{i}"}
                for i in range(10)
            ]
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = fake_data
        mock_response.raise_for_status = MagicMock()

        async def mock_get(url, **kwargs):
            return mock_response

        with patch.object(provider, "_get_client") as mock_client:
            client_instance = MagicMock()
            client_instance.get = mock_get
            mock_client.return_value = client_instance

            results = asyncio.run(provider.search("test", limit=3))

        assert len(results) == 3

    def test_search_connect_error_returns_empty(self) -> None:
        """Verify ConnectError returns [] instead of raising."""
        import httpx
        provider = self._make_provider()

        async def mock_get(url, **kwargs):
            raise httpx.ConnectError("Connection refused")

        with patch.object(provider, "_get_client") as mock_client:
            client_instance = MagicMock()
            client_instance.get = mock_get
            mock_client.return_value = client_instance

            results = asyncio.run(provider.search("test"))

        assert results == []

    # ------------------------------------------------------------------ #
    # healthcheck() tests
    # ------------------------------------------------------------------ #

    def test_healthcheck_ok(self) -> None:
        import httpx
        provider = self._make_provider()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200

        async def mock_get(url, **kwargs):
            return mock_response

        with patch.object(provider, "_get_client") as mock_client:
            client_instance = MagicMock()
            client_instance.get = mock_get
            mock_client.return_value = client_instance

            status = asyncio.run(provider.healthcheck())

        assert status == ProviderStatus.OK

    def test_healthcheck_unavailable_on_connect_error(self) -> None:
        import httpx
        provider = self._make_provider()

        async def mock_get(url, **kwargs):
            raise httpx.ConnectError("refused")

        with patch.object(provider, "_get_client") as mock_client:
            client_instance = MagicMock()
            client_instance.get = mock_get
            mock_client.return_value = client_instance

            status = asyncio.run(provider.healthcheck())

        assert status == ProviderStatus.UNAVAILABLE

    def test_healthcheck_timeout(self) -> None:
        import httpx
        provider = self._make_provider()

        async def mock_get(url, **kwargs):
            raise httpx.TimeoutException("timeout")

        with patch.object(provider, "_get_client") as mock_client:
            client_instance = MagicMock()
            client_instance.get = mock_get
            mock_client.return_value = client_instance

            status = asyncio.run(provider.healthcheck())

        assert status == ProviderStatus.TIMEOUT

    # ------------------------------------------------------------------ #
    # close() tests
    # ------------------------------------------------------------------ #

    def test_close_when_no_client(self) -> None:
        provider = self._make_provider()
        asyncio.run(provider.close())  # Should not raise


class TestSearXNGRegistryIntegration:
    """Tests for SearXNG provider via the registry."""

    def test_registry_returns_searxng(self) -> None:
        from aideator.search.registry import get_search_provider
        from aideator.search.searxng import SearXNGSearchProvider

        provider = get_search_provider({"search_provider": "searxng", "searxng_instance_url": "http://localhost:8080"})
        assert isinstance(provider, SearXNGSearchProvider)
        assert provider.name == "searxng"

    def test_registry_custom_url_via_dict(self) -> None:
        import os

        from aideator.search.registry import get_search_provider

        with patch.dict(os.environ, {"SEARXNG_URL": "http://custom:9999"}):
            provider = get_search_provider({"search_provider": "searxng"})
        assert provider._instance_url == "http://custom:9999"

    def test_registry_lists_searxng(self) -> None:
        from aideator.search.registry import list_available_search_providers

        providers = list_available_search_providers()
        names = [p["name"] for p in providers]
        assert "searxng" in names

        sxng = next(p for p in providers if p["name"] == "searxng")
        assert sxng["requires_api_key"] is False
        assert sxng["tier"] == "self-hosted"
