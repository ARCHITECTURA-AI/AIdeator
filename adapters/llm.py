"""LLM adapter for legacy compatibility.

This module provides backward compatibility for existing code.
New code should use the LLM provider system from aideator.llm.
"""

from __future__ import annotations

import asyncio
from typing import Any

from aideator.llm.providers import LLMResponse, ProviderConfig
from aideator.llm.registry import get_provider
from api.config import settings


def extract_text(response: dict[str, Any]) -> str:
    """Extract text from a raw LLM response.

    Args:
        response: Raw response dict from LLM API

    Returns:
        Extracted text content
    """
    return str(response["choices"][0]["message"]["content"])


def extract_text_from_response(response: LLMResponse) -> str:
    """Extract text from LLMResponse.

    Args:
        response: LLMResponse object

    Returns:
        Text content
    """
    return response.content


async def generate_text(
    messages: list[dict[str, str]],
    provider: str | None = None,
    model: str | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """Generate text using configured LLM provider.

    This is a convenience function that uses the provider registry.

    Args:
        messages: List of message dicts with 'role' and 'content'
        provider: Override provider name (optional)
        model: Override model name (optional)
        **kwargs: Additional parameters (temperature, max_tokens, etc.)

    Returns:
        LLMResponse with generated content
    """
    # Use overrides or fall back to settings
    provider_name = provider or settings.llm_provider
    model_name = model or settings.llm_model

    # Build config dict for get_provider
    config_dict = {
        "llm_provider": provider_name,
        "llm_model": model_name,
        "llm_api_base": settings.llm_api_base,
        "llm_api_key": settings.llm_api_key,
    }

    llm = get_provider(config_dict)
    return await llm.generate(messages, **kwargs)


def generate_text_sync(
    messages: list[dict[str, str]],
    provider: str | None = None,
    model: str | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """Synchronous wrapper for generate_text.

    Args:
        messages: List of message dicts with 'role' and 'content'
        provider: Override provider name (optional)
        model: Override model name (optional)
        **kwargs: Additional parameters

    Returns:
        LLMResponse with generated content
    """
    return asyncio.run(generate_text(messages, provider, model, **kwargs))


async def check_provider_health(provider: str | None = None) -> dict[str, Any]:
    """Check health of an LLM provider.

    Args:
        provider: Provider name (uses settings if not specified)

    Returns:
        Dictionary with health status and metadata
    """
    provider_name = provider or settings.llm_provider

    config_dict = {
        "llm_provider": provider_name,
        "llm_model": settings.llm_model,
        "llm_api_base": settings.llm_api_base,
        "llm_api_key": settings.llm_api_key,
    }

    llm = get_provider(config_dict)
    status = await llm.healthcheck()

    return {
        "provider": provider_name,
        "status": status.value,
        "is_healthy": status == status.__class__.OK,
        "metadata": llm.metadata(),
    }


# Legacy compatibility aliases
get_llm_response = generate_text_sync

__all__ = [
    "extract_text",
    "extract_text_from_response",
    "generate_text",
    "generate_text_sync",
    "check_provider_health",
    "get_llm_response",
]
