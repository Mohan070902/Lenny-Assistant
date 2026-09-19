from app.providers.base import BaseLLMProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.cloud_provider import CloudProvider
from app.config import get_settings

def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    settings = get_settings()
    selected = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower().strip()
    
    if selected in ["cloud", "claude", "openai", "gemini", "anthropic"]:
        return CloudProvider(provider_type=selected)
    
    # Default to Ollama local
    return OllamaProvider()
