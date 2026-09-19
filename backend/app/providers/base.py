from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Any

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        """Stream generated tokens from the LLM provider."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is operational and configured."""
        pass
