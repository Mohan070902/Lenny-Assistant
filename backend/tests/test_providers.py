import pytest
from app.providers.factory import get_llm_provider
from app.providers.ollama_provider import OllamaProvider
from app.providers.cloud_provider import CloudProvider

def test_provider_factory_default():
    provider = get_llm_provider("ollama")
    assert isinstance(provider, OllamaProvider)
    assert provider.model is not None

def test_provider_factory_cloud():
    provider = get_llm_provider("cloud")
    assert isinstance(provider, CloudProvider)

@pytest.mark.asyncio
async def test_ollama_provider_unreachable():
    # Points to non-existent port to test resilience
    provider = OllamaProvider(base_url="http://localhost:59999", model="llama3.2:3b")
    available = await provider.is_available()
    assert available is False

    tokens = []
    async for token in provider.generate_response([{"role": "user", "content": "hello"}], "system"):
        tokens.append(token)
    
    full_text = "".join(tokens)
    assert "Unreachable" in full_text or "Ollama" in full_text

@pytest.mark.asyncio
async def test_cloud_provider_missing_keys():
    # Test safe feedback when no keys are configured
    provider = CloudProvider()
    provider.anthropic_key = ""
    provider.openai_key = ""
    provider.gemini_key = ""

    available = await provider.is_available()
    assert available is False

    tokens = []
    async for token in provider.generate_response([{"role": "user", "content": "test"}], "system"):
        tokens.append(token)

    full_text = "".join(tokens)
    assert "Not Configured" in full_text
