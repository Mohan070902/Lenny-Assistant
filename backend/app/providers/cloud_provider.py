import json
import logging
import httpx
from typing import AsyncGenerator, Dict, List
from app.providers.base import BaseLLMProvider
from app.config import get_settings

logger = logging.getLogger("cloud_provider")

class CloudProvider(BaseLLMProvider):
    def __init__(self, provider_type: str = "auto"):
        settings = get_settings()
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.anthropic_model = settings.ANTHROPIC_MODEL
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL
        self.provider_type = provider_type

    async def is_available(self) -> bool:
        return bool(self.anthropic_key or self.openai_key or self.gemini_key)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        if self.anthropic_key:
            async for token in self._stream_anthropic(messages, system_prompt, temperature):
                yield token
        elif self.openai_key:
            async for token in self._stream_openai(messages, system_prompt, temperature):
                yield token
        elif self.gemini_key:
            async for token in self._stream_gemini(messages, system_prompt, temperature):
                yield token
        else:
            yield (
                "\n\n⚠️ **Cloud Provider Not Configured:** No cloud API key was detected in your environment.\n\n"
                "To enable cloud LLM inference, configure one of the following in your `.env` file:\n"
                "- `ANTHROPIC_API_KEY=your_key_here`\n"
                "- `OPENAI_API_KEY=your_key_here`\n"
                "- `GEMINI_API_KEY=your_key_here`\n\n"
                "In the meantime, you can switch to **Local (Ollama)** from the model selector dropdown."
            )

    async def _stream_anthropic(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Format messages for Anthropic
        anthropic_msgs = []
        for m in messages:
            if m["role"] in ["user", "assistant"]:
                anthropic_msgs.append({"role": m["role"], "content": m["content"]})
        
        payload = {
            "model": self.anthropic_model,
            "system": system_prompt,
            "messages": anthropic_msgs,
            "max_tokens": 4096,
            "temperature": temperature,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield f"\n\n**Anthropic API Error ({resp.status_code}):** {error_body.decode('utf-8')}"
                        return

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            event = json.loads(data_str)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Anthropic streaming exception: {e}")
            yield f"\n\n**Cloud API Error:** {str(e)}"

    async def _stream_openai(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.openai_model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "temperature": temperature,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield f"\n\n**OpenAI API Error ({resp.status_code}):** {error_body.decode('utf-8')}"
                        return

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            event = json.loads(data_str)
                            choices = event.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"OpenAI streaming exception: {e}")
            yield f"\n\n**Cloud API Error:** {str(e)}"

    async def _stream_gemini(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:streamGenerateContent?key={self.gemini_key}&alt=sse"
        headers = {"Content-Type": "application/json"}
        
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })
        
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": temperature}
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield f"\n\n**Gemini API Error ({resp.status_code}):** {error_body.decode('utf-8')}"
                        return

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        try:
                            event = json.loads(data_str)
                            candidates = event.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    text = p.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Gemini streaming exception: {e}")
            yield f"\n\n**Cloud API Error:** {str(e)}"
