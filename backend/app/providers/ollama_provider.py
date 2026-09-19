import json
import logging
import httpx
from typing import AsyncGenerator, Dict, List
from app.providers.base import BaseLLMProvider
from app.config import get_settings

logger = logging.getLogger("ollama_provider")

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = None, model: str = None):
        settings = get_settings()
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m.get("name") for m in data.get("models", [])]
        except Exception:
            pass
        return []

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": True,
            "options": {"temperature": temperature}
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code == 404:
                        yield (
                            f"\n\n**Ollama Model Notice:** The requested model `{self.model}` was not found on your local Ollama instance.\n"
                            f"To pull it, run: `ollama run {self.model}` in your terminal."
                        )
                        return

                    if response.status_code != 200:
                        yield f"\n\n**Ollama Error:** Service returned status code {response.status_code}."
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            yield (
                "\n\n⚠️ **Local Ollama Unreachable:** Could not connect to Ollama at `" + self.base_url + "`.\n\n"
                "Please verify that Ollama is installed and running:\n"
                "1. Start the Ollama application or run `ollama serve` in a terminal.\n"
                "2. Ensure you have pulled the model with `ollama pull " + self.model + "`.\n"
                "3. Alternatively, switch to the Cloud model option in the top bar."
            )
        except httpx.TimeoutException:
            yield "\n\n⚠️ **Ollama Request Timed Out:** The local model took too long to respond. You may need a smaller model (e.g. `llama3.2:3b`)."
        except Exception as e:
            logger.error(f"Unexpected Ollama exception: {e}")
            yield f"\n\n⚠️ **Ollama Error:** {str(e)}"
