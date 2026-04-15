"""LLM Provider implementations.

Provides concrete implementations for various LLM backends:
- OllamaProvider: Local Ollama API
- OpenAICompatibleProvider: OpenAI-compatible APIs (OpenAI, Groq, Mistral, Anthropic, etc.)
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

import httpx


class ProviderStatus(Enum):
    """Health check status for LLM providers."""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True)
class LLMResponse:
    """Standardized LLM response.

    Attributes:
        content: The generated text content
        model: The model used for generation
        provider: The provider name
        usage: Token usage information (optional)
        latency_ms: Request latency in milliseconds
        raw_response: Original provider response (for debugging)
    """

    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None
    latency_ms: float = 0.0
    raw_response: dict[str, Any] | None = None

    @property
    def text(self) -> str:
        """Alias for content."""
        return self.content


@dataclass
class ProviderConfig:
    """Configuration for LLM providers.

    Attributes:
        provider: Provider type (ollama, openai-compatible, etc.)
        model: Model name/identifier
        api_base: Base URL for API
        api_key: API key (if required)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
    """

    provider: str
    model: str
    api_base: str
    api_key: str = ""
    timeout: float = 120.0
    max_retries: int = 3
    extra_headers: dict[str, str] | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement:
    - generate(): Generate text from messages
    - healthcheck(): Check provider availability
    - metadata(): Get provider metadata
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        """Provider name."""
        return self.config.provider

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
                (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with generated content and metadata
        """
        ...

    @abstractmethod
    async def healthcheck(self) -> ProviderStatus:
        """Check if the provider is healthy and available.

        Returns:
            ProviderStatus indicating health state
        """
        ...

    def metadata(self) -> dict[str, Any]:
        """Get provider metadata.

        Returns:
            Dictionary with provider information
        """
        return {
            "name": self.config.provider,
            "model": self.config.model,
            "api_base": self.config.api_base,
            "local_only_ok": self.is_local,
            "requires_api_key": self.requires_api_key,
        }

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """Whether this provider works without external API calls."""
        ...

    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        ...

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.extra_headers:
                headers.update(self.config.extra_headers)
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client connections."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> LLMProvider:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()


class OllamaProvider(LLMProvider):
    """Provider for local Ollama instances.

    Ollama runs locally and provides OpenAI-compatible API.
    Default base URL: http://localhost:11434
    """

    DEFAULT_API_BASE = "http://localhost:11434"
    GENERATE_ENDPOINT = "/api/chat"

    def __init__(self, config: ProviderConfig) -> None:
        # Set default base URL if not provided
        if not config.api_base:
            config = ProviderConfig(
                provider=config.provider,
                model=config.model,
                api_base=self.DEFAULT_API_BASE,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        super().__init__(config)

    @property
    def is_local(self) -> bool:
        """Ollama is a local provider."""
        return True

    @property
    def requires_api_key(self) -> bool:
        """Ollama doesn't require an API key for local use."""
        return False

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using Ollama API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options (temperature, stream, etc.)

        Returns:
            LLMResponse with generated content
        """
        client = await self._get_client()
        url = f"{self.config.api_base}{self.GENERATE_ENDPOINT}"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = kwargs["max_tokens"]

        start_time = time.time()

        for attempt in range(self.config.max_retries):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000

                content = data.get("message", {}).get("content", "")
                if not content:
                    content = data.get("response", "")

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    provider=self.config.provider,
                    usage=data.get("prompt_eval_count") or data.get("eval_count"),
                    latency_ms=latency_ms,
                    raw_response=data,
                )
            except httpx.TimeoutException:
                if attempt == self.config.max_retries - 1:
                    raise
                await self._backoff(attempt)
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.config.max_retries - 1:
                    await self._backoff(attempt)
                else:
                    raise

        raise RuntimeError("Max retries exceeded")

    async def healthcheck(self) -> ProviderStatus:
        """Check if Ollama is running."""
        try:
            client = await self._get_client()
            # Ollama doesn't have a dedicated health endpoint, so we list models
            url = f"{self.config.api_base}/api/tags"
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                return ProviderStatus.OK
            return ProviderStatus.ERROR
        except httpx.ConnectError:
            return ProviderStatus.UNAVAILABLE
        except httpx.TimeoutException:
            return ProviderStatus.TIMEOUT
        except Exception:
            return ProviderStatus.ERROR

    async def list_models(self) -> list[str]:
        """List available models from Ollama.

        Returns:
            List of model names
        """
        try:
            client = await self._get_client()
            url = f"{self.config.api_base}/api/tags"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            return []

    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff between retries."""
        import asyncio

        wait_time = min(2**attempt, 30)  # Max 30 seconds
        await asyncio.sleep(wait_time)


class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs.

    Supports:
    - OpenAI (https://api.openai.com/v1)
    - Groq (https://api.groq.com/openai/v1)
    - Mistral (https://api.mistral.ai/v1)
    - Anthropic via proxy
    - Any OpenAI-compatible endpoint
    """

    DEFAULT_API_BASE = "https://api.openai.com/v1"
    CHAT_ENDPOINT = "/chat/completions"

    def __init__(self, config: ProviderConfig) -> None:
        # Set default base URL if not provided
        if not config.api_base:
            config = ProviderConfig(
                provider=config.provider,
                model=config.model,
                api_base=self.DEFAULT_API_BASE,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        super().__init__(config)

    @property
    def is_local(self) -> bool:
        """OpenAI-compatible providers are external."""
        return False

    @property
    def requires_api_key(self) -> bool:
        """OpenAI-compatible providers require an API key."""
        return True

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using OpenAI-compatible API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with generated content
        """
        client = await self._get_client()
        url = f"{self.config.api_base}{self.CHAT_ENDPOINT}"

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]

        start_time = time.time()

        for attempt in range(self.config.max_retries):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage")

                return LLMResponse(
                    content=content,
                    model=data.get("model", self.config.model),
                    provider=self.config.provider,
                    usage=usage,
                    latency_ms=latency_ms,
                    raw_response=data,
                )
            except httpx.TimeoutException:
                if attempt == self.config.max_retries - 1:
                    raise
                await self._backoff(attempt)
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.config.max_retries - 1:
                    await self._backoff(attempt)
                else:
                    raise

        raise RuntimeError("Max retries exceeded")

    async def healthcheck(self) -> ProviderStatus:
        """Check if the API is accessible.

        Returns:
            ProviderStatus indicating health state
        """
        if not self.config.api_key:
            return ProviderStatus.NOT_CONFIGURED

        try:
            client = await self._get_client()
            # Try to list models as a health check
            url = f"{self.config.api_base}/models"
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                return ProviderStatus.OK
            elif response.status_code == 401:
                return ProviderStatus.ERROR
            return ProviderStatus.ERROR
        except httpx.ConnectError:
            return ProviderStatus.UNAVAILABLE
        except httpx.TimeoutException:
            return ProviderStatus.TIMEOUT
        except Exception:
            return ProviderStatus.ERROR

    async def list_models(self) -> list[str]:
        """List available models from the API.

        Returns:
            List of model IDs
        """
        try:
            client = await self._get_client()
            url = f"{self.config.api_base}/models"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception:
            return []

    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff between retries."""
        import asyncio

        wait_time = min(2**attempt, 30)  # Max 30 seconds
        await asyncio.sleep(wait_time)


class AnthropicCompatibleProvider(OpenAICompatibleProvider):
    """Provider for Anthropic Claude via OpenAI-compatible proxy.

    Anthropic has its own API format, but many proxies expose it
    as OpenAI-compatible. This provider handles Anthropic-specific
    configurations.
    """

    DEFAULT_API_BASE = "https://api.anthropic.com/v1"

    def __init__(self, config: ProviderConfig) -> None:
        # Anthropic uses x-api-key header
        extra_headers = config.extra_headers or {}
        extra_headers["x-api-key"] = config.api_key
        extra_headers["anthropic-version"] = "2023-06-01"

        super().__init__(
            ProviderConfig(
                provider=config.provider,
                model=config.model,
                api_base=config.api_base or self.DEFAULT_API_BASE,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
                extra_headers=extra_headers,
            )
        )

    @property
    def requires_api_key(self) -> bool:
        """Anthropic requires an API key."""
        return True


class MistralCompatibleProvider(OpenAICompatibleProvider):
    """Provider for Mistral AI API.

    Mistral has an OpenAI-compatible API with some specific features.
    """

    DEFAULT_API_BASE = "https://api.mistral.ai/v1"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(
            ProviderConfig(
                provider=config.provider,
                model=config.model,
                api_base=config.api_base or self.DEFAULT_API_BASE,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        )

    @property
    def requires_api_key(self) -> bool:
        """Mistral requires an API key."""
        return True
