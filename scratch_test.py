from api.config import settings

object.__setattr__(settings, 'llm_provider', 'mock')
print("patched:", settings.llm_provider)
object.__setattr__(settings, 'llm_provider', 'ollama')
print("restored:", settings.llm_provider)
