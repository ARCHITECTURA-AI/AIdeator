"""LLM Provider registry for dynamic provider loading.

Maps provider names to provider classes and handles configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.config import Settings

from aideator.llm.providers import (
    AnthropicCompatibleProvider,
    LLMProvider,
    MistralCompatibleProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    ProviderConfig,
)

# Registry mapping provider names to classes
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai-compatible": OpenAICompatibleProvider,
    "openai": OpenAICompatibleProvider,
    "anthropic-compatible": AnthropicCompatibleProvider,
    "anthropic": AnthropicCompatibleProvider,
    "mistral-compatible": MistralCompatibleProvider,
    "mistral": MistralCompatibleProvider,
    "groq": OpenAICompatibleProvider,
}


def get_provider(settings: Settings | dict[str, str]) -> LLMProvider:
    """Get an LLM provider instance based on settings.

    Args:
        settings: Settings object or dict with provider configuration.
            Expected keys: llm_provider, llm_model, llm_api_base, llm_api_key

    Returns:
        Configured LLMProvider instance

    Raises:
        ValueError: If provider is not registered
    """
    # Handle both Settings object and dict
    if isinstance(settings, dict):
        provider_name = settings.get("llm_provider", "ollama")
        model = settings.get("llm_model", "mistral:7b")
        api_base = settings.get("llm_api_base", "")
        api_key = settings.get("llm_api_key", "")
    else:
        # It's a Settings object
        provider_name = settings.llm_provider
        model = settings.llm_model
        api_base = settings.llm_api_base
        api_key = settings.llm_api_key

    provider_class = PROVIDER_REGISTRY.get(provider_name)
    if provider_class is None:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Available providers: {available}"
        )

    config = ProviderConfig(
        provider=provider_name,
        model=model,
        api_base=api_base,
        api_key=api_key,
        timeout=120.0,
        max_retries=3,
    )

    return provider_class(config)


def list_available_providers() -> list[dict[str, str | bool]]:
    """List all available LLM providers.

    Returns:
        List of provider metadata dictionaries
    """
    providers = []
    for name, provider_class in PROVIDER_REGISTRY.items():
        # Create a dummy config to get metadata
        dummy_config = ProviderConfig(
            provider=name,
            model="default",
            api_base="",
        )
        instance = provider_class(dummy_config)
        metadata = instance.metadata()
        providers.append({
            "name": name,
            "local_only_ok": metadata["local_only_ok"],
            "requires_api_key": metadata["requires_api_key"],
            "default_base": metadata["api_base"],
        })
    return providers


def register_provider(name: str, provider_class: type[LLMProvider]) -> None:
    """Register a custom provider.

    Args:
        name: Provider name/identifier
        provider_class: LLMProvider subclass

    Raises:
        ValueError: If name is already registered
    """
    if name in PROVIDER_REGISTRY:
        raise ValueError(f"Provider '{name}' is already registered")
    PROVIDER_REGISTRY[name] = provider_class


def get_provider_info(provider_name: str) -> dict[str, str | bool] | None:
    """Get information about a specific provider.

    Args:
        provider_name: Name of the provider

    Returns:
        Provider info dict or None if not found
    """
    provider_class = PROVIDER_REGISTRY.get(provider_name)
    if provider_class is None:
        return None

    dummy_config = ProviderConfig(
        provider=provider_name,
        model="default",
        api_base="",
    )
    instance = provider_class(dummy_config)
    return instance.metadata()


def is_local_provider(provider_name: str) -> bool:
    """Check if a provider is local-only.

    Args:
        provider_name: Name of the provider

    Returns:
        True if provider is local-only, False otherwise
    """
    provider_class = PROVIDER_REGISTRY.get(provider_name)
    if provider_class is None:
        return False

    dummy_config = ProviderConfig(
        provider=provider_name,
        model="default",
        api_base="",
    )
    instance = provider_class(dummy_config)
    return instance.is_local
