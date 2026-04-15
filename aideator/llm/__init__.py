"""LLM Provider module for AIdeator.

Provides pluggable LLM providers with a common interface:
- OllamaProvider: For local Ollama instances
- OpenAICompatibleProvider: For OpenAI, Groq, Mistral, Anthropic proxies, etc.
"""

from __future__ import annotations

from aideator.llm.providers import (
    LLMProvider,
    LLMResponse,
    OllamaProvider,
    OpenAICompatibleProvider,
    ProviderStatus,
)
from aideator.llm.registry import get_provider, list_available_providers

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "ProviderStatus",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "get_provider",
    "list_available_providers",
]
