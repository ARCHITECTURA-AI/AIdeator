from typing import Any

from aideator.llm.providers import LLMProvider, LLMResponse, ProviderStatus


class MockLLMProvider(LLMProvider):
    """Mock LLM Provider for testing."""
    
    def __init__(self, config=None):
        from aideator.llm.providers import ProviderConfig
        if config is None:
            config = ProviderConfig(provider="mock", model="mock", api_base="")
        super().__init__(config)
        self.responses = []
        self.default_response = '{"status": "ok"}'

    @property
    def is_local(self) -> bool:
        return True

    @property
    def requires_api_key(self) -> bool:
        return False

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        content = self.responses.pop(0) if self.responses else self.default_response
        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.config.provider,
            latency_ms=10.0
        )

    async def healthcheck(self) -> ProviderStatus:
        return ProviderStatus.OK
