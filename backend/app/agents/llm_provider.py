import httpx
import json
from typing import Optional, AsyncIterator
from app.config import settings
import structlog

logger = structlog.get_logger()


class OllamaProvider:
    """Async wrapper around the Ollama REST API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = settings.OLLAMA_TIMEOUT
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        model = model or settings.OLLAMA_REASONING_MODEL
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            response = await self._client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.HTTPError as e:
            logger.error("Ollama generate failed", error=str(e), model=model)
            raise

    async def embed(self, text: str, model: Optional[str] = None) -> list[float]:
        model = model or settings.OLLAMA_EMBED_MODEL
        try:
            response = await self._client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            response.raise_for_status()
            return response.json().get("embedding", [])
        except httpx.HTTPError as e:
            logger.error("Ollama embed failed", error=str(e), model=model)
            raise

    async def close(self):
        await self._client.aclose()


# Module-level singleton
_provider: Optional[OllamaProvider] = None


def get_llm_provider() -> OllamaProvider:
    global _provider
    if _provider is None:
        _provider = OllamaProvider()
    return _provider
