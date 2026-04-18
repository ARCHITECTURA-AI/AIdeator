"""Unit tests for LLM provider infrastructure."""

from __future__ import annotations

import pytest

from aideator.llm.providers import (
    LLMResponse,
    ProviderConfig,
    ProviderStatus,
)
from aideator.llm.registry import get_provider, list_available_providers


class TestProviderConfig:
    """Tests for ProviderConfig construction."""

    def test_defaults(self) -> None:
        config = ProviderConfig(
            provider="ollama", model="mistral:7b", api_base="http://localhost:11434"
        )
        assert config.api_key == ""
        assert config.timeout == 120.0
        assert config.max_retries == 3
        assert config.extra_headers is None

    def test_full_config(self) -> None:
        config = ProviderConfig(
            provider="openai-compatible",
            model="gpt-4o",
            api_base="https://api.openai.com/v1",
            api_key="sk-test-123",
            timeout=60.0,
            max_retries=5,
        )
        assert config.provider == "openai-compatible"
        assert config.api_key == "sk-test-123"
        assert config.timeout == 60.0


class TestLLMResponse:
    """Tests for LLMResponse data class."""

    def test_basic_response(self) -> None:
        resp = LLMResponse(
            content="Hello world",
            model="test-model",
            provider="test",
        )
        assert resp.content == "Hello world"
        assert resp.text == "Hello world"  # Alias
        assert resp.model == "test-model"

    def test_with_usage(self) -> None:
        resp = LLMResponse(
            content="test",
            model="m",
            provider="p",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            latency_ms=150.5,
        )
        assert resp.usage is not None
        assert resp.usage["prompt_tokens"] == 10
        assert resp.latency_ms == 150.5

    def test_frozen(self) -> None:
        resp = LLMResponse(content="test", model="m", provider="p")
        with pytest.raises(AttributeError):
            resp.content = "changed"  # type: ignore[misc]


class TestProviderStatus:
    """Tests for ProviderStatus enum."""

    def test_all_values(self) -> None:
        assert ProviderStatus.OK.value == "ok"
        assert ProviderStatus.ERROR.value == "error"
        assert ProviderStatus.TIMEOUT.value == "timeout"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"
        assert ProviderStatus.NOT_CONFIGURED.value == "not_configured"


class TestListAvailableProviders:
    """Tests for LLM provider listing."""

    def test_returns_list(self) -> None:
        providers = list_available_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0

    def test_has_required_keys(self) -> None:
        providers = list_available_providers()
        for p in providers:
            assert "name" in p
            assert "requires_api_key" in p

    def test_ollama_local_only_ok(self) -> None:
        providers = list_available_providers()
        ollama = [p for p in providers if p["name"] == "ollama"]
        assert len(ollama) > 0
        assert ollama[0]["local_only_ok"] is True

    def test_cloud_providers_require_key(self) -> None:
        providers = list_available_providers()
        cloud = [
            p for p in providers
            if p["name"] in ("openai-compatible", "anthropic-compatible", "mistral-compatible")
        ]
        for p in cloud:
            assert p["requires_api_key"] is True


class TestGetProvider:
    """Tests for provider instantiation via registry."""

    def test_ollama_instance(self) -> None:
        """Ollama provider should instantiate without API key."""
        provider = get_provider({
            "llm_provider": "ollama",
            "llm_model": "mistral:7b",
            "llm_api_base": "http://localhost:11434",
            "llm_api_key": "",
        })
        assert provider.name == "ollama"
        assert provider.is_local is True
        assert provider.requires_api_key is False

    def test_openai_compatible_instance(self) -> None:
        """OpenAI-compatible should instantiate with key."""
        provider = get_provider({
            "llm_provider": "openai-compatible",
            "llm_model": "gpt-4o",
            "llm_api_base": "https://api.openai.com/v1",
            "llm_api_key": "sk-test-key",
        })
        assert provider.name == "openai-compatible"
        assert provider.is_local is False
        assert provider.requires_api_key is True

    def test_metadata_returns_dict(self) -> None:
        provider = get_provider({
            "llm_provider": "ollama",
            "llm_model": "test",
            "llm_api_base": "http://localhost:11434",
            "llm_api_key": "",
        })
        meta = provider.metadata()
        assert isinstance(meta, dict)
        assert "name" in meta
        assert "model" in meta
        assert "local_only_ok" in meta
